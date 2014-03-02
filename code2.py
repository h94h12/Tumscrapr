import web
from web import form
from tumscrape import compare

render = web.template.render('templates/')

urls = ('/', 'index')
app = web.application(urls, globals())

myform = form.Form( 
    form.Textbox("user1"), 
    form.Textbox("user2")) 

class index: 
    def GET(self): 
        form = myform()
        # make sure you create a copy of the form by calling it (line above)
        # Otherwise changes will appear globally
        return render.formtest(form)

    def POST(self): 
        form = myform() 
        if not form.validates(): 
            return render.formtest(form)
        else:
            # form.d.boe and form['boe'].value are equivalent ways of
            # extracting the validated arguments from the form.
            data = compare(form['user1'].value, form['user2'].value)
	    match = data[0]
	    user1_urls = data[1]
	    user2_urls = data[2] 
	    # return "The match percent between %s and %s is %s" % (form['user1'].value, form['user2'].value, match)
	    return render.results(match, user1_urls, user2_urls) 	

	
if __name__=="__main__":
    web.internalerror = web.debugerror
    app.run()
