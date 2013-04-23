#!/usr/bin/env python
#
# Copyright 2012 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from apiclient.discovery import build
from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from oauth2client.appengine import oauth2decorator_from_clientsecrets
from oauth2client.client import AccessTokenRefreshError
from webapp2_extras import json
import httplib2
import jinja2
import logging
import os
import pickle
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

#CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'local_secrets.json')
CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secrets.json')

# Helpful message to display in the browser if the CLIENT_SECRETS file
# is missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
<h1>Warning: Please configure OAuth 2.0</h1>
<p>
To make this sample run you will need to populate the client_secrets.json file
found at:
</p>
<code>%s</code>
<p>You can find the Client ID and Client secret values
on the API Access tab in the <a
href="https://code.google.com/apis/console">APIs Console</a>.
</p>

""" % CLIENT_SECRETS


http = httplib2.Http(memcache)
service = build("tasks", "v1", http=http)


decorator = oauth2decorator_from_clientsecrets(
    CLIENT_SECRETS,
    scope=[
      'https://www.googleapis.com/auth/tasks',
      'https://www.googleapis.com/auth/tasks.readonly',
    ],
    message=MISSING_CLIENT_SECRETS_MESSAGE)

class TasklistsHandler(webapp2.RequestHandler):

  @decorator.oauth_required
  def get(self):    
    http = httplib2.Http()
    http = decorator.credentials.authorize(http)  
    service = build("tasks", "v1", http=http)
        
    tasklists_request = service.tasklists().list(pageToken=None, maxResults=None)    
    tasklists_response = tasklists_request.execute()
       
    template_values = {
            'tasklists': tasklists_response["items"],
    }
    template = JINJA_ENVIRONMENT.get_template('template/tasklists.html')
    self.response.write(template.render(template_values))
    
class TasksHandler(webapp2.RequestHandler):

  @decorator.oauth_required
  def get(self, tasklist_id):   
    http = httplib2.Http()
    http = decorator.credentials.authorize(http)
    service = build("tasks", "v1", http=http)
        
    tasks_request = service.tasks().list(tasklist=tasklist_id, pageToken=None, maxResults=None)   
    tasks_response = tasks_request.execute()
    
    template_values = {
            'tasklist_id': tasklist_id,
            'tasks': tasks_response["items"]
    }
    template = JINJA_ENVIRONMENT.get_template('template/tasks.html')
    self.response.write(template.render(template_values))
    
  @decorator.oauth_required
  def post(self, tasklist_id):  
    http = httplib2.Http()
    http = decorator.credentials.authorize(http)
    service = build("tasks", "v1", http=http)
    
    title = self.request.get('title')
    task = {
      'title': title,
    }

    task_insert = service.tasks().insert(tasklist=tasklist_id, body=task, parent=None, previous=None)
    task_insert.execute()

    self.redirect('/lists/'+tasklist_id+'/tasks')
    

app = webapp2.WSGIApplication(
      [
       (r'/', TasklistsHandler),
       (r'/lists/(\w+)/tasks', TasksHandler),
       (decorator.callback_path, decorator.callback_handler()),
      ],
      debug=True)

