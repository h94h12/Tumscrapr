import web

t_globals = dict(
	datestr=web.datestr,
)

render = web.template.render('templates/',
globals = t_globals)
render._keywords['globals']['render'] = render

def listing(**k):
	return rend.listing('stuff') 
