import scraper
import bs4
from selenium import webdriver
import shutil
import requests
import matches
import similar
import sys 

def get_img_posts(username):
	url = 'http://{}.tumblr.com/archive'.format(username)
	driver = scraper.get_driver()
	process = lambda soup:[parse_post(post) for post in soup.select('div.post')]
	results = scraper.process_whole_page(driver,
		url, process)
	return results
		
def parse_post(post):
	try:
		img = post.find('div', 
		{'class': 'post_thumbnail_container has_imageurl'}
		).attrs['data-imageurl']
		return img
	except Exception:
		return ' '

def load_image(url, name):
	response = requests.get(url, stream=True)
	with open('{}.png'.format(name), 'wb') as out_file:
		shutil.copyfileobj(response.raw, out_file)	
#a and b are the two names to compare
#size is the min size of each of the sets
#assume images are named as such: a1.png, b1.png, etc. 
def compare_image_sets(a, b, size):
	max_matches = []
	for i in range(0, size):
		max_match = 0 
		#iterating through a. compare one image in a to every image in b.
		#find highest match between a and b, and add to max_matches 
		for j in range(0, size):
			max_match = max(max_match, 
					similar.similarness(a+str(i)+'.png', 
							    b+str(j)+'.png'))
			max_matches.append(max_match) 
					
	average = (float)(sum(max_matches))/len(max_matches)
	return average
			
def compare(a, b):
	other = a
        my = b

        other_imgs = [post for post in get_img_posts(other) if post is not ' ']
        my_imgs = [post for post in get_img_posts(my) if post is not ' ']
        size = min(len(other_imgs), len(my_imgs))

        for i in range(0,size):
                m = 'me{}'.format(i)
                o = 'other{}'.format(i)
                print 'Downloading:  '+my_imgs[i]+'   '+other_imgs[i]
                load_image(my_imgs[i], m)
                load_image(other_imgs[i], o)
        average = compare_image_sets('me', 'other', size)
        print 'The match percent is {}'.format(average)
	return average

if __name__ == '__main__':
	other = str(sys.argv[1])
	my = str(sys.argv[2])

	other_imgs = [post for post in get_img_posts(other) if post is not ' ']
	my_imgs = [post for post in get_img_posts(my) if post is not ' ']
	size = min(len(other_imgs), len(my_imgs))
	
	for i in range(0,size):
		m = 'me{}'.format(i)
		o = 'other{}'.format(i)
		print 'Downloading:  '+my_imgs[i]+'   '+other_imgs[i]
		load_image(my_imgs[i], m)
		load_image(other_imgs[i], o)
	average = compare_image_sets('me', 'other', size) 
	print 'The match percent is {}'.format(average) 
