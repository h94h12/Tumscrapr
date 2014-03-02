# coding=utf-8

#!/usr/bin/python
import time
import bs4
import pymongo
from selenium import webdriver
import traceback

def get_driver(driver_width=6000, driver_height=3000, limit=3):
    connections_attempted = 0
    while connections_attempted < limit:
    	try:
    		driver = webdriver.PhantomJS(service_args=['--load-images=no'])
    		driver.set_window_size(driver_width, driver_height)
    		return driver
    	except Exception as e:
		connections_attempted += 1
            	print('Getting driver again...')
           	print('  connections attempted: {}'.format(connections_attempted))
            	print('  exception message: {}'.format(e))
		traceback.print_exc()	


# for any results page, the web driver scrolls down until the number of
# results reaches the limit (limit is 500 or 1000 depending on time of day...)
#for now, get users for a query
def process_whole_page(driver, url, process, limit=500,
                       connections_to_attempt=3, scrolls_to_attempt=3,
                       sleep_interval=2):
    """
    Process the whole page at url with the given function, making sure
    that at least limit results have been processed -- or that there
    are less than limit results on the page.
    To do this, we scroll down the page with driver.

    Parameters
    ----------
    driver: selenium.webdriver
    url: string
    process: function
        Text fetched by driver is processed by this.
        Returns a list.
    limit: int
        Until we get this many results, or become certain that there
        aren't this many results at the url, we will keep scrolling the
        driver.
    connections_to_attempt: int
    scrolls_to_attempt: int
    sleep_interval: float
        Sleep this number of seconds between tries.

    Returns
    -------
    results: list or None
        Whatever the process function returns.

    Raises
    ------
    e: Exception
        If connection times out more than connections_to_attempt
    """
    assert(scrolls_to_attempt > 0)
    assert(limit > 0)
    driver = get_driver()
    connections_attempted = 0
    while connections_attempted < connections_to_attempt:
        try:
            
            driver.get(url)
            soup = bs4.BeautifulSoup(driver.page_source)
	    results = process(soup)
            all_scrolls_attempted = 0

            # If we fetch more than limit results already, we're done.
            # Otherwise, try to get more results by scrolling.
            # We give up after some number of scroll tries.
            # If we do get more results, then the scroll count resets.
            if len(results) < limit:
                scrolls_attempted = 0
                while (scrolls_attempted < scrolls_to_attempt and
                       len(results) < limit):
                    all_scrolls_attempted += 1
                    scrolls_attempted += 1

                    # Scroll and parse results again.
                    # The old results are still on the page, so it's fine
                    # to overwrite.
                    driver.execute_script(
                        "window.scrollTo(0, document.body.scrollHeight);")
                    soup = bs4.BeautifulSoup(driver.page_source)
                    new_results = process(soup)

                    if len(new_results) > len(results):
                        results = new_results
                        scrolls_attempted = 0

            print('Obtained {} results after {} scrolls'.format(
                len(results), all_scrolls_attempted))
            if len(results) > limit:
                results = results[:limit]
            return results

        except Exception as e:
            connections_attempted += 1
            print('URL failed: {}'.format(url))
            print('  connections attempted: {}'.format(connections_attempted))
            print('  exception message: {}'.format(e))
	    
            traceback.print_exc()
	    time.sleep(sleep_interval)
            driver = get_driver()
	    #from IPython import embed
	    #embed()
    print('URL skipped: {}'.format(url))
    return None


def parse_board(board, username, source):
    """
    Parameters
    ----------
    board: some kind of bs4 object

    Returns
    -------
    data: dict
    """
    num_pins = board.select('.boardPinCount')[0].text.strip()
    num_pins = num_pins.split(' ')[0].replace(',', '')
    data = {
        'username': username,
        'source': source,
        'board_url': 'www.pinterest.com{}'.format(
            board.find_all('a', {'class': 'boardLinkWrapper'})[0].get('href')),
        'board_name': board.select('.boardName .title')[0].text.strip(),
        'cover_img': board.select('img')[0]['src'],
        'thumb_imgs': [_['src'] for _ in board.select('img')[1:]],
        'num_pins': int(num_pins)
    }
    data['_id'] = data['board_url']
    return data


def scrape_user_boards(driver, username, source):
    """
    Return all boards of the user.

    Parameters
    ----------
    username: string
    source: string
        Describes why this user's boards are getting scraped:
        - "query: <whatever>"
        - "follower of: <username>"

    Returns
    -------
    boards: list of dicts
    """
    url = 'http://www.pinterest.com/{}/boards/'.format(username)
    boards = process_whole_page(
        driver, url, lambda soup: [
            parse_board(board, username, source)
            for board in soup.select('div.item')
        ])
    return boards


#scrape the list of followers of a user
# (get first 50 for now)
#query: query associated with username
def get_followers(driver, username, query):
    url = 'http://www.pinterest.com/{}/followers/'.format(username)
    g = lambda soup: [
        link['href'].split('/')[1]
        for link in soup.findAll('a', {'class': 'userWrapper'})
    ]
    followers = process_whole_page(driver, url, g, 30, True)
    return followers


def get_usernames_from_query_results_page(driver, url, limit=500):
    # Parse the usernames, which exist as the last part of hrefs in
    # .boardLinkWrapper <a> tags.
    get_usernames = lambda soup: [
        link['href'].split('/')[1]
        for link in soup.findAll('a', {'class': 'boardLinkWrapper'})
    ]
    usernames = process_whole_page(driver, url, get_usernames, limit)
    return usernames


def scrape_query(query, board_collection, user_collection, user_limit=500):
    """
    Find all users with a board matching the query, and scrape all of
    their boards, inserting them into board_collection.

    If user is already present in user_collection, it means that we
    have scraped their boards, and so do not need to scrape again -- but
    do need to update their record with this query.
    """
    print(u'scrape_query: on {}'.format(query))

    driver = get_driver()
    url = 'http://www.pinterest.com/search/boards/?q=' + query
    usernames = get_usernames_from_query_results_page(driver, url, user_limit)

    # For each user, scrape their boards page, or update their record.
    for username in usernames:
        # If we've already scraped this user's boards, then we don't
        # need to do that again, but we note that we have seen this
        # user for this new query.
        username_count = user_collection.find(
            {'username': username}).limit(1).count()
        if username_count > 0:
            # TODO: confirm that this appends to list of queries
            # because it looks like it just overwrites it
	    if query in user_collection.find_one({'username': username})['query']:
            	print('Already ran query {} for user {}'.format(query, username))
            print("Not scraping boards of user {}".format(username))
            user_collection.update(
                {'username': username}, {'$push': {'query': query}})

        # Otherwise, we scrape the user's boards.
        else:
            boards = scrape_user_boards(
                driver, username, 'query: {} '.format(query))
            if len(boards) > 0:
                user_collection.insert({
                    'username': username,
                    'num_boards': len(boards),
                    'query': [query]
                })
                for board in boards:
                    try:
                        board_collection.insert(board)
                    except pymongo.errors.DuplicateKeyError:
                        continue
                print('Inserted {} from {} with query: {}'.format(
                    len(boards), username, query))
queries = [
        'pastel',
        'melancholy',
        'hdr',
        'noir',
        'soft',
        'macro',
        'horror',
        'sunny',
        'serene',
        'hazy',
        'bright',
        'energetic',
        'ethereal', 'vintage', 'depth of field',
        'long Exposure', 'geometric composition',
        'minimal',
        'romantic',
        'bokeh', 'detailed',
        'washed out', 'texture',
        'instagram',
        'sepia', 'black and white', 'corporate', 'industrial',
        'organic',
	'nature', 'portrait', 
	'landscape', 'animals',
        'happy', 'scary', 'sad', 'calm', 'upbeat', 'pensive',
        'tense', 'futuristic', 'sleek', 'radiant', 'fall',
        'summer', 'winter', 'spring', 'cloudy',
        'night'
    ]

if __name__ == '__main__':
    # TODO: make capitalization consistent
    
    driver = get_driver()
    client = pymongo.MongoClient('localhost', 27017)
    db = client['pinscraping_3']

    user_collection = db['users']
    user_collection.ensure_index('username')
    board_collection = db['boards']
    for query in queries:
        query = query.lower()
        scrape_query(query, board_collection, user_collection)

    print 'DONE SCRAPING. These urls failed'
