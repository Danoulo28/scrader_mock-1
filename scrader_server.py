from __future__ import print_function
import flask
import json
import math
import socket
from flask.ext.cors import CORS
from flask import request
import os
import signal
import copy
import websites
from scrader_logger import LOG
import mongo
import utils

DEBUG = False  # Enable this to print python crashes and exceptions

app = flask.Flask(__name__, static_url_path='/static')

# Make cross-origin AJAX possible (for all domains on all routes)
CORS(app, resources={r"*": {"origins": "*"}})

Server_url = "https://webview.scrader.com"


@app.route('/scrader/companies/<user_id>'.format(methods=['GET']))
def get_companies_html(user_id):
    """ GET Server Status API endpoint
        Args:
        Returns:
            dict: A JSON object containing the nfvacc server status information
    """
    first_name = "None"
    user = mongo.find_one_match('users', {"user_id": user_id})
    if user is not None:
        last_name = user.get('name')
        first_name = user.get('first_name', last_name)

    return flask.render_template('companies.html', name=first_name, user_id=user_id)


@app.route('/scrader/datetime/<user_id>'.format(methods=['GET']))
def get_datetime_html(user_id):
    """ GET Server Status API endpoint
        Args:
        Returns:
            dict: A JSON object containing the nfvacc server status information
    """
    first_name = "None"
    user = mongo.find_one_match('users', {"user_id": user_id})
    if user is not None:
        last_name = user.get('name')
        first_name = user.get('first_name', last_name)

    return flask.render_template('new_time.html', name=first_name, user_id=user_id)


@app.route('/scrader/websites/<user_id>'.format(methods=['GET']))
def get_websites_html(user_id):
    """ GET Server Status API endpoint
        Args:
        Returns:
            dict: A JSON object containing the nfvacc server status information
    """
    first_name = "None"
    user = mongo.find_one_match('users', {"user_id": user_id})
    if user is not None:
        last_name = user.get('name')
        first_name = user.get('first_name', last_name)

    return flask.render_template('websites.html', name=first_name, user_id=user_id)


@app.route('/scrader/all_companies'.format(methods=['GET']))
def get_all_companies():
    """ GET Server Status API endpoint
        Args:
        Returns:
            dict: A JSON object containing the nfvacc server status information
    """

    response_data = utils.get_all_companies()

    status = 200 if response_data is not None else 403
    js = json.dumps(response_data, indent=2)
    return flask.Response(js, status=status, mimetype='application/json')


@app.route('/scrader/search_company'.format(methods=['GET']))
def company_search():
    """ GET Server Status API endpoint
        Args:
        Returns:
            dict: A JSON object containing the nfvacc server status information
    """
    LOG.info('request received')
    company_typed = (request.args.get('last user freeform input')).lower()
    LOG.info(company_typed)
    LOG.info('searching for {}'.format(company_typed))
    first_name = request.args.get('first name')
    user_id = request.args.get('chatfuel user id')

    user = mongo.find_one_match('users', {"user_id": user_id})
    if company_typed == 'dev':
        return development_mode(user)
   
    if user is not None:
        mongo.remove_one_from('users', {"user_id": user_id}, {'request': 1})
    
        if company_typed == 'hi':
            buttons = []
            notifications_button = {
                "type": "web_url",
                "url": "{}/scrader/companies/{}".format(Server_url, user_id),
                "title": "Edit Notifications"
            }
            message = 'Just pick one of the options below or type a listed company name for our full relevant articles archive.'
            block = 'Companies'
            button_title = 'Good/Neutral News'
            button_dict_tmpl = {
                "type": "show_block",
                "block_name": block,
                "title": button_title
            }
            buttons.append(button_dict_tmpl)

            block = 'Companies'
            button_title = 'Bad News'
            button_dict_tmpl = {
                "type": "show_block",
                "block_name": block,
                "title": button_title
            }
            buttons.append(button_dict_tmpl)
            buttons.append(notifications_button)
            response_data = {
                "messages": [
                    {
                        "attachment": {
                            "type": "template",
                            "payload": {
                               "template_type": "button",
                               "text": message,
                               "buttons": buttons
                            }
                        }
                     }
                ]
            }
            status = 200 if response_data is not None else 403
            js = json.dumps(response_data, indent=2)
            return flask.Response(js, status=status, mimetype='application/json')
    # print(user_id)
    company_found = utils.company_typed_search(company_typed)
    if company_found is not None:
        company_for_url = "+".join(company_found.split())
        if company_typed != company_found.lower():
            response_data = {
                "messages": [{
                    "text":
                    "Did you mean {}?".format(company_found),
                    "quick_replies": [{
                        "title":
                        "Yes",
                        "url":
                        '{}/company_specific/{}/{}/{}'.format(
                            Server_url, company_for_url, user_id, 'all_news'),
                        "type":
                        "json_plugin_url"
                    }, {
                        "title": "Not really...",
                        "block_names": ["Default"]
                    }]
                }]
            }

        else:
            return specific_company(company_for_url, user_id, 'all_news')

    else:
        buttons = []

        message = "I am sorry {}, there is no match for your request. " \
                  "You can choose one of the following options " \
                  "or try typing a listed company name, once more.".format(
                      first_name)

        block = 'Companies'
        button_title = 'Good/Neutral News'
        button_dict_tmpl = {
            "type": "show_block",
            "block_name": block,
            "title": button_title
        }
        buttons.append(button_dict_tmpl)

        block = 'Companies'
        button_title = 'Bad News'
        button_dict_tmpl = {
            "type": "show_block",
            "block_name": block,
            "title": button_title
        }
        buttons.append(button_dict_tmpl)

        response_data = {
            "messages": [{
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "button",
                        "text": message,
                        "buttons": buttons
                    }
                }
            }]
        }

    status = 200 if response_data is not None else 403
    js = json.dumps(response_data, indent=2)
    return flask.Response(js, status=status, mimetype='application/json')


def development_mode(user):
    # print(user.get('name'))
    num_positive, num_negative = utils.find_num_of_tagged()
    message = 'Just got into development mode. ' \
              'Until now there are {} positive manually tagged articles' \
              ' and {} negative manually tagged articles in our database.' \
              ' Try to keep these two values balanced in order Scrader to be' \
              ' trained correctly!' \
              ' Now which articles you want to check?'.\
              format(num_positive, num_negative)
    buttons = []
    button_dict_tmpl = {
        'type': "json_plugin_url",
        'title': 'Positive Predictions',
        'url': "{}/dev_news/{}/{}/{}".format(Server_url, 'POS', 1,
                                             user.get('name'))
    }
    buttons.append(button_dict_tmpl)
    button_dict_tmpl = {
        'type': "json_plugin_url",
        'title': 'Negative Predictions',
        'url': "{}/dev_news/{}/{}/{}".format(Server_url, 'NEG', 1,
                                             user.get('name'))
    }
    buttons.append(button_dict_tmpl)

    response_data = {
        "messages": [{
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "button",
                    "text": message,
                    "buttons": buttons
                }
            }
        }]
    }
    # response_data = utils.get_development_news(1)
    # print(response_data)
    status = 200 if response_data is not None else 403
    js = json.dumps(response_data, indent=2)
    # print(js)
    return flask.Response(js, status=status, mimetype='application/json')


@app.route('/dev_news/<news_type>/<page_num>/<user>'.format(methods=['GET']))
def get_development_news(news_type, page_num, user):
    """ GET Server Status API endpoint
        Args:
        Returns:
            dict: A JSON object containing the nfvacc server status information
    """
    LOG.info('request received')
    response_data = utils.get_development_news(news_type, page_num, user)
    status = 200 if response_data is not None else 403
    js = json.dumps(response_data, indent=2)
    # print(js)
    return flask.Response(js, status=status, mimetype='application/json')


@app.route('/scrader/all_websites'.format(methods=['GET']))
def get_all_websites():
    """ GET Server Status API endpoint
        Args:
        Returns:
            dict: A JSON object containing the nfvacc server status information
    """

    response_data = websites.all_websites

    status = 200 if response_data is not None else 403
    js = json.dumps(response_data, indent=2)
    return flask.Response(js, status=status, mimetype='application/json')


@app.route('/login/<user_id>/<user_name>/<last_name>', methods=['POST', 'GET'])
def user_login(user_id, user_name, last_name):
    """ GET Server Status API endpoint
        Args:
        Returns:
            dict: A JSON object containing the nfvacc server status information
    """
    LOG.info("Hi from {}".format(socket.gethostname()))
    # name = user_name
    registered = False
    first_time = True

    user = mongo.find_one_match('users', {"user_id": user_id})
    if user is not None:
        first_time = False
        first_name = user.get('first_name')
        if user.get('subscribed'):
            registered = True
    else:
        user_dict = {
            'first_name': user_name,
            'last_name': last_name,
            'subscribed': False,
            'user_id': user_id
        }
        mongo.insert_one('users', user_dict)

    buttons = []
    init_message = ''
    if first_time:
        # init_message = 'Hi!Nice to meet you ....! ' \
        #                'Yes, I am just a machine, ' \
        #                'but I can show you news from listed companies daily...' \
        #                'I can even decide which news are bad news!'

        message = 'Let the magic begin! Pick one of the options ' \
                  'below or simply type any a listed company name.'

        button_title = 'Notifications'
        button_dict_tmpl = {
            "type": "web_url",
            "url": "{}/scrader/companies/{}".format(Server_url, user_id),
            "title": button_title
        }

        buttons.append(button_dict_tmpl)
        block = 'Initializition'
        button_title = 'I am just a guest'
        button_dict_tmpl = {
            "type": "show_block",
            "block_name": block,
            "title": button_title
        }
        buttons.append(button_dict_tmpl)
    else:
        block = 'Companies'
        button_title = 'Good/Neutral News'
        button_dict_tmpl = {
            "type": "show_block",
            "block_name": block,
            "title": button_title
        }
        buttons.append(button_dict_tmpl)

        block = 'Companies'
        button_title = 'Bad News'
        button_dict_tmpl = {
            "type": "show_block",
            "block_name": block,
            "title": button_title
        }
        buttons.append(button_dict_tmpl)

        if registered:
            # message = 'Hi again {}. What would you like me to show you? ' \
            #           'Remember you can type any company you want to search for scraped news'.\
            #           format(first_name)

            message = 'Welcome back {}! ' \
                      'Hungry for more news? '\
                      'Just pick one of the options below or type ' \
                      'a listed company name for our full relevant articles archive.'.format(
                          first_name)

            notifications_button = {
                "type": "web_url",
                "url": "{}/scrader/companies/{}".format(Server_url, user_id),
                "title": "Edit Notifications"
            }
            buttons.append(notifications_button)
        else:
            # message = 'Hi again {}. What would you like me to show you? ' \
            #           'Remember you can type any company you want to search for scraped news'.\
            #           format(name)
            message = 'Welcome back {}! ' \
                      'Hungry for more news? '\
                      'Just pick one of the options below or type ' \
                      'a listed company name for our full relevant articles archive.'.format(
                          first_name)
            notifications_button = {
                "type": "web_url",
                "url": "{}/scrader/companies/{}".format(Server_url, user_id),
                "title": "Notifications"
            }
            buttons.append(notifications_button)
    if init_message != '':
        response_data = {
            "messages": [
                {'text': init_message},
                {
                    "attachment": {
                        "type": "template",
                        "payload": {
                            "template_type": "button",
                            "text": message,
                            "buttons": buttons
                        }
                    }
                }
            ]
        }
    else:
        response_data = {
            "messages": [
                {
                    "attachment": {
                        "type": "template",
                        "payload": {
                            "template_type": "button",
                            "text": message,
                            "buttons": buttons
                        }
                    }
                }
            ]
        }

    # print(response_data)
    status = 200 if response_data is not None else 403
    js = json.dumps(response_data, indent=2)
    return flask.Response(js, status=status, mimetype='application/json')


@app.route(
    '/subscribe/<user_id>/<user_last_name>/<user_first_name>',
    methods=['POST'])
def subscribe(user_id, user_last_name, user_first_name):
    """ GET Server Status API endpoint
        Args:
        Returns:
            dict: A JSON object containing the nfvacc server status information
    """

    user = mongo.find_one_match('users', {"user_id": user_id})
    if user is not None:
        mongo.insert_one_in('users', {"user_id": user_id}, {
                            'name': user_last_name})
        mongo.insert_one_in('users', {"user_id": user_id}, {
                            'subscribed': True})

    response_data = {}
    status = 200 if response_data is not None else 403
    js = json.dumps(response_data, indent=2)
    return flask.Response(js, status=status, mimetype='application/json')


@app.route('/status'.format(methods=['GET']))
def get_server_status():
    """ GET Server Status API endpoint
        Args:
        Returns:
            dict: A JSON object containing the nfvacc server status information
    """
    LOG.info('status request received')
    response_data = {'server_status': 'OK'}
    status = 200 if response_data is not None else 403
    js = json.dumps(response_data, indent=2)
    return flask.Response(js, status=status, mimetype='application/json')


@app.route('/scrader/user_companies', methods=['POST'])
def user_companies_data():
    """ GET Server Status API endpoint
        Args:
        Returns:
            dict: A JSON object containing the nfvacc server status information
    """

    data = flask.request.get_json()

    user_id = data.get('user')

    user = mongo.find_one_match('users', {"user_id": user_id})
    if user is not None:
        mongo.insert_one_in('users', {"user_id": user_id}, {
                            'subscribed': True})
        mongo.insert_one_in('users', {"user_id": user_id}, {
                            'companies': data.get('companies')})
        mongo.insert_one_in('users', {"user_id": user_id}, {
                            'notification_type': 'Companies'})

    response_data = {}
    status = 200 if response_data is not None else 403
    js = json.dumps(response_data, indent=2)
    return flask.Response(js, status=status, mimetype='application/json')


@app.route('/scrader/user_datetime', methods=['POST'])
def user_datetime_data():
    """ GET Server Status API endpoint
        Args:
        Returns:
            dict: A JSON object containing the nfvacc server status information
    """

    data = flask.request.get_json()
    user_id = data.get('user')
    LOG.info(data)
    conv_datetime = utils.convert_time(data.get('datetime'), data.get('offset'))
    LOG.info(conv_datetime)
    user = mongo.find_one_match('users', {"user_id": user_id})
    if user is not None:
        mongo.insert_one_in('users', {"user_id": user_id}, {
                            'datetime': conv_datetime})
        mongo.insert_one_in('users', {"user_id": user_id}, {
                            'offset': data.get('offset')})


    # user = mongo.find_one_match('users', {"user_id": user_id})
    # utils.start_scheduler_task(user)
    response_data = {}
    status = 200 if response_data is not None else 403
    js = json.dumps(response_data, indent=2)
    return flask.Response(js, status=status, mimetype='application/json')


@app.route('/scrader/user_datetime/<user_id>', methods=['GET'])
def get_user_datetime_data(user_id):
    """ GET Server Status API endpoint
        Args:
        Returns:
            dict: A JSON object containing the nfvacc server status information
    """

    user = mongo.find_one_match('users', {"user_id": user_id})
    datetime = ''
    if user is not None:
        datetime = user.get('datetime', False)
        if datetime:
            offset = - int(user.get('offset', 0))
            datetime = utils.convert_time(datetime, offset)

    response_data = datetime
    status = 200 if response_data is not None else 403
    js = json.dumps(response_data, indent=2)
    return flask.Response(js, status=status, mimetype='application/json')


@app.route('/scrader/modify_user/<user_id>/<company_name>/<action>', methods=['GET'])
def modify_user_companies(user_id, company_name, action):
    """ GET Server Status API endpoint
        Args:
        Returns:
            dict: A JSON object containing the nfvacc server status information
    """
    company_net = " ".join(company_name.split('+'))
    response_data = {}

    user = mongo.find_one_match('users', {"user_id": user_id})
    if user is not None:
        user_name = user.get('first_name')
        if action == 'add':
            user['companies'].append(company_net)
            message = "{} now on you will be notified for {} too.".format(
                user_name, company_net)
        else:
            user['companies'].remove(company_net)
            message = "{} now on you won't be notified for {}.".format(
                user_name, company_net)

        mongo.insert_one_in('users', {"user_id": user_id}, {
                            'companies': user['companies']})

        response_data = {"messages": [{"text": message}]}

    # print(response_data)
    status = 200 if response_data is not None else 403
    js = json.dumps(response_data, indent=2)
    return flask.Response(js, status=status, mimetype='application/json')


@app.route('/scrader/user_websites', methods=['POST'])
def user_websites_data():
    """ GET Server Status API endpoint
        Args:
        Returns:
            dict: A JSON object containing the nfvacc server status information
    """

    data = flask.request.get_json()

    user_id = data.get('user')
    user = mongo.find_one_match('users', {"user_id": user_id})
    if user is not None:
        mongo.insert_one_in('users', {"user_id": user_id}, {
                            'websites': data.get('websites')})

    response_data = {}
    status = 200 if response_data is not None else 403
    js = json.dumps(response_data, indent=2)
    return flask.Response(js, status=status, mimetype='application/json')


@app.route('/companies/<user_id>', methods=['GET'])
def user_companies(user_id):
    """ GET Server Status API endpoint
        Args:
        Returns:
            dict: A JSON object containing the nfvacc server status information
    """

    subscribed_companies = []
    user = mongo.find_one_match('users', {"user_id": user_id})
    if user is not None:
        subscribed_companies = user.get('companies', [])

    # print(subscribed_companies)
    response_data = subscribed_companies
    status = 200 if response_data is not None else 403
    js = json.dumps(response_data, indent=2)
    return flask.Response(js, status=status, mimetype='application/json')


@app.route('/websites/<user_id>', methods=['GET'])
def user_websites(user_id):
    """ GET Server Status API endpoint
        Args:
        Returns:
            dict: A JSON object containing the nfvacc server status information
    """

    subscribed_websites = []
    user = mongo.find_one_match('users', {"user_id": user_id})
    if user is not None:
        subscribed_websites = user.get('websites', [])

    response_data = subscribed_websites
    status = 200 if response_data is not None else 403
    js = json.dumps(response_data, indent=2)
    return flask.Response(js, status=status, mimetype='application/json')

# TODO remove


@app.route('/user_notification/<user_id>/<time_frame>'.format(methods=['GET']))
def user_notification(user_id, time_frame):
    """ GET Server Status API endpoint
        Args:
        Returns:
            dict: A JSON object containing the nfvacc server status information
    """

    user = mongo.find_one_match('users', {"user_id": user_id})
    user_name = user.get('first_name', user_id)

    if time_frame == 'Daily':
        mongo.insert_one_in('users', {"user_id": user_id}, {
                            'notification_type': 'Daily'})
        message = "{} you will be notified {}".format(user_name, time_frame)
        response_data = {"messages": [{"text": message}]}
    else:

        mongo.insert_one_in('users', {"user_id": user_id}, {
                            'notification_type': 'Companies'})
        response_data = {
            "messages": [{
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type":
                        "generic",
                        "elements": [{
                            "title":
                            "See scrader's supported companies",
                            "buttons": [{
                                "type":
                                "web_url",
                                "url":
                                "{}/scrader/companies/{}".
                                format(Server_url, user_id),
                                "title":
                                "Go Now"
                            }]
                        }]
                    }
                }
            }]
        }

    status = 200 if response_data is not None else 403
    js = json.dumps(response_data, indent=2)
    return flask.Response(js, status=status, mimetype='application/json')


@app.route('/user_daily_notification/<user_id>'.format(methods=['GET']))
def user_daily_notification(user_id):
    """ GET Server Status API endpoint
        Args:
        Returns:
            dict: A JSON object containing the nfvacc server status information
    """

    user = mongo.find_one_match('users', {"user_id": user_id})
    datetime = user.get('datetime')
    offset = - int(user.get('offset'))
    datetime = utils.convert_time(datetime, offset)

    message = 'You will be notified daily @ {} for the companies you have selected'.\
              format(datetime)

    buttons = []
    block = 'News'
    button_title = "Today's News"
    button_dict_tmpl = {
        "type": "show_block",
        "block_name": block,
        "title": button_title
    }
    buttons.append(button_dict_tmpl)

    extra_button = {}
    extra_button['type'] = "web_url"
    extra_button['title'] = 'Edit Notifications'
    extra_button['url'] = "{}/scrader/companies/{}".format(Server_url, user_id)
    buttons.append(extra_button)

    response_data = {
        "messages": [
            {"text": message},
            {"attachment": {
                "type": "template",
                "payload": {
                    "template_type":
                        "button",
                    "text":
                        "Now how would you like to continue?",
                    "buttons": buttons
                }
            }
            }
        ]
    }

    status = 200 if response_data is not None else 403
    js = json.dumps(response_data, indent=2)
    return flask.Response(js, status=status, mimetype='application/json')


@app.route('/company_specific/<company>/<user_id>/<news_time>'.format(methods=['GET']))
def specific_company(company, user_id, news_time):
    """ GET Server Status API endpoint
        Args:
        Returns:
            dict: A JSON object containing the nfvacc server status information
    """
    LOG.info("Fetching for company {}.".format(company))
    company_for_url = company
    company = " ".join(company.split('+'))
    subscribed = False
    followed = False
    user_request = None
    title = ''
    user = mongo.find_one_match('users', {"user_id": user_id})
    if user is not None:
        if user.get('notification_type') == 'Companies':
            subscribed = True
            if company in user.get('companies'):
                followed = True
        user_request = user.get('request', None)

    extra_button = {}

    if subscribed:
        if not followed:
            extra_button['type'] = "json_plugin_url"
            extra_button['title'] = 'Follow'
            extra_button['url'] = "{}/scrader/modify_user/{}/{}/add".\
                format(Server_url, user_id, company_for_url)

    company_given = company
    type_of_news = utils.company_news_type(company_given, news_time)

    if type_of_news:
        one_news_type = True
        if len(type_of_news) > 1:
            type_of_news.sort(reverse=True)
            one_news_type = False

        news_buttons = []
        for news_type in type_of_news:
            if news_type == 'good_companies':
                title = "Good/Neutral News"
                new_button = {
                    "type": "show_block",
                    "block_names": ["Fetch news"],
                    "title": title
                }
                news_buttons.append(new_button)
            else:
                title = "Bad News"
                new_button = {
                    "type": "show_block",
                    "block_names": ["Fetch news"],
                    "title": title
                }
                news_buttons.append(new_button)

        if extra_button:
            if one_news_type:
                arg = new_button.get('title').split()[0]
                LOG.info('one news type %s', arg.lower())
                return helper_function(extra_button, company, arg.lower(), news_time)

        indication_message = {}
        if not one_news_type:
            if user_request is not None:
                if user_request == 'Good/Neutral News':
                    user_request = 'negative'
                else:
                    user_request = 'positive'
                indication_message = {
                    "text": 'There are also {} news for {}'.format(user_request, company)}
        # print(news_buttons)
        if news_time == 'today':
            mess = "Which {} news would you like to see from my today's archive?".format(
                company)
        else:
            mess = "Which {} news would you like to see from my full archive?".format(
                company)

        response_data = {
            "set_attributes": {
                "company_requested": company,
                "news_time": news_time,
            },
            "messages": [{
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type":
                        "button",
                        "text":
                        mess,
                        "buttons": news_buttons
                    }
                }
            }]
        }

        if extra_button:
            response_data['messages'][0]['attachment']['payload']['buttons'].append(
                extra_button)
        else:
            if one_news_type:
                title_butt = news_buttons[0]['title'].split()
                news_type = title_butt[0].lower()
                if news_type == "good/neutral":
                    new_type = 'good'
                else:
                    new_type = 'bad'
                LOG.info('one news type: calling get news %s', new_type)
                return get_news(company_for_url, new_type, 1, news_time)

        if indication_message:
            response_data['messages'].insert(0, indication_message)

    else:
        negative_message = {"text": 'No articles found about {}'.format(company)}
        response_data = {
            "set_attributes": {
                "company_requested": company
            },
            "messages": [negative_message]
        }
        if extra_button:
            extra_message = {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type":
                            "button",
                        "text":
                            "Remember you can {} {}.".format(
                                extra_button.get('title').lower(), company),
                        "buttons": [extra_button]
                    }
                }
            }
            response_data['messages'].append(extra_message)

    status = 200 if response_data is not None else 403
    js = json.dumps(response_data, indent=2)
    return flask.Response(js, status=status, mimetype='application/json')


def helper_function(extra_button, company, news_type, news_time):

    message = {
        "attachment": {
            "type": "template",
            "payload": {
                "template_type": "button",
                "text": "Remember you can follow {}".format(company),
                "buttons": [
                    extra_button
                ]
            }
        }
    }
    if news_type == "good/neutral":
        news_type = 'good'
    else:
        news_type = 'bad'
    company = "+".join(company.split())
    LOG.info('inside helper func: calling get news %s', news_type)
    return get_news(company, news_type, message, news_time)


@app.route('/get_latest_new/<user_id>/<new_id>'.format(methods=['GET']))
def get_specific_new(user_id, new_id):
    LOG.info('Finding new with id {}'.format(new_id))
    article = utils.find_one_article(new_id)
    LOG.info(article)
    elements = [{
        "title": article.get('title')[0:79],
        "image_url": str(article.get('image_url')),
        "subtitle": article.get('subtitle'),
        "item_url": str(article.get('item_url')),
        "buttons": [{
            "type": "web_url",
            "url": article.get('website_url'),
            "title": article.get('website')
        }]
    }]

    top_message = {"text": 'One new {} article found about {}'.
                   format(article.get('direction'), article.get('company'))}
    messages = [
        top_message,
        {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": elements
                }
            }
        }
    ]

    response_data = {"messages": messages}
    status = 200 if response_data is not None else 403
    js = json.dumps(response_data, indent=2)
    return flask.Response(js, status=status, mimetype='application/json')


@app.route('/get_user_companies_news/<user_id>/<page_num>'.format(methods=['GET']))
def get_user_companies_news(user_id, page_num):

    user = mongo.find_one_match('users', {"user_id": user_id})
    elements = []
    element = {
        "title": '',
        "image_url": '',
        "subtitle": '',
        "item_url": '',
        "buttons": [{
            "type": "web_url",
            "url": '',
            "title": ''
        }]
    }

    messages = []
    message = {
        "attachment": {
            "type": "template",
            "payload": {
                "template_type": "generic",
                "elements": elements
            }
        }
    }

    quick_replies = []
    quick_reply = {"title": '', "url": '', "type": "json_plugin_url"}

    companies_list = user.get('companies')
    requested_news = utils.get_all_news_for_companies(companies_list)
    if not requested_news:
        # negative_message = {"text": 'Unfortunately no articles were'
        #                     ' found today for the companies you have selected.'}
        response_data = {
            #"messages": [negative_message]
        }
    else:
        f = lambda A, n=10: [A[i:i + n] for i in range(0, len(A), n)]
        news_per_page = f(requested_news)
        LOG.info(page_num)
        news_to_show = news_per_page[int(page_num) - 1]
        all_quick_replies_page_numbers = [
            i + 1 for i, _ in enumerate(news_per_page)
        ]
        quick_replies_page_numbers_to_show = filter(lambda x: x != int(page_num),
                                                    all_quick_replies_page_numbers)

        for new in news_to_show:
            company = new.get('company')
            if new.get('direction') == "POS":
                sentiment = "Positive"
            else:
                sentiment = "Negative"
            element = copy.deepcopy(element)
            element['title'] = (new.get('title')[0:79]).strip()
            element['image_url'] = str(new.get('image_url'))
            #element['subtitle'] = new.get('subtitle')
            element['subtitle'] = "{} article about {}".format(sentiment, company)
            element['item_url'] = str(new.get('item_url'))
            element['buttons'][0]['url'] = new.get('website_url')
            element['buttons'][0]['title'] = new.get('website')
            #element['buttons'][0]['title'] = "See {} new".format(sentiment)
            elements.append(element)

        LOG.info('quick_replies_page_numbers_to_show: {}'.
                 format(quick_replies_page_numbers_to_show))
        # quick replies cannot be over 11
        if len(quick_replies_page_numbers_to_show) > 11:
            quick_replies_page_numbers_to_show = quick_replies_page_numbers_to_show[:11]
        for page_number in quick_replies_page_numbers_to_show:
            quick_reply = copy.deepcopy(quick_reply)
            quick_reply['title'] = "Page {}".format(page_number)
            quick_reply['url'] = "{}/get_user_companies_news/{}/{}".\
                                 format(Server_url, user_id, page_number)
            quick_replies.append(quick_reply)

        if quick_replies:
            message['quick_replies'] = quick_replies

        message['attachment']['payload']['elements'] = elements

        article = 'articles' if len(requested_news) > 1 else 'article'
        top_message = {"text": '{} {} found today'.
                       format(len(requested_news), article)}

        if int(page_num) == 1:
            messages.append(top_message)

        # print(message)
        messages.append(message)

        response_data = {"messages": messages}

    # print(response_data)
    status = 200 if response_data is not None else 403
    js = json.dumps(response_data, indent=2)
    return flask.Response(js, status=status, mimetype='application/json')


@app.route('/news/<company>/<news_type>/<page_num>/<date>'.format(methods=['GET']))
def get_news(company, news_type, page_num, date):
    """ GET Server Status API endpoint
        Args:
        Returns:
            dict: A JSON object containing the nfvacc server status information
    """

    # print(
    #     "Fetching {} news for {} page {}".format(news_type, company, page_num))
    if news_type == 'news':
        news_type = request.args.get('news_type')
    else:
        if news_type == 'good':
            news_type = 'Good/Neutral News'
        else:
            news_type = 'Bad News'
    company_net = " ".join(company.split('+'))
    LOG.info("Fetching {} news for {} page {}".format(
        news_type, company, page_num))
    extra_message = {}
    if isinstance(page_num, dict):
        extra_message = page_num
        page_num = 1

    elements = []
    element = {
        "title": '',
        "image_url": '',
        "subtitle": '',
        "item_url": '',
        "buttons": [{
            "type": "web_url",
            "url": '',
            "title": ''
        }]
    }

    messages = []
    message = {
        "attachment": {
            "type": "template",
            "payload": {
                "template_type": "generic",
                "elements": elements
            }
        }
    }

    quick_replies = []
    quick_reply = {"title": '', "url": '', "type": "json_plugin_url"}
    LOG.info(news_type)
    if news_type == 'positive' or news_type == 'Good/Neutral News' or news_type == 'good/neutral':
        news_message = 'Positive'
        direction_list = ['POS', 'POSITIVE']
        _news_type = 'good'
    else:
        news_message = 'Negative'
        direction_list = ['NEG', 'NEGATIVE']
        _news_type = 'bad'
    LOG.info(direction_list)
    LOG.info('requested news for %s %s', company_net, date)
    requested_news = utils.get_news_by_direction_and_company(
        company_net, direction_list, date)
    requested_news = order_news_by_date(requested_news)
    f = lambda A, n=10: [A[i:i + n] for i in range(0, len(A), n)]
    news_per_page = f(requested_news)
    # print(news_per_page)
    news_to_show = news_per_page[int(page_num) - 1]
    # print(news_to_show)
    all_quick_replies_page_numbers = [
        i + 1 for i, _ in enumerate(news_per_page)
    ]
    # print(all_quick_replies_page_numbers)
    quick_replies_page_numbers_to_show = filter(lambda x: x != int(page_num),
                                                all_quick_replies_page_numbers)
    # print(quick_replies_page_numbers_to_show)

    for new in news_to_show:
        element = copy.deepcopy(element)
        element['title'] = (new.get('title')[0:79]).strip()
        element['image_url'] = str(new.get('image_url'))
        element['subtitle'] = new.get('subtitle')
        element['item_url'] = str(new.get('item_url'))
        element['buttons'][0]['url'] = new.get('website_url')
        element['buttons'][0]['title'] = new.get('website')
        # id = str(new.get('_id'))
        # element['buttons'][0]['url'] = "https://webview.scrader.com/taged_article/{}".format(id)
        # element['buttons'][0]['title'] = "Wrong Sentiment?"
        # element['buttons'][0]['type'] = "json_plugin_url"
        elements.append(element)

    LOG.info('quick_replies_page_numbers_to_show: {}'.
             format(quick_replies_page_numbers_to_show))
    # quick replies cannot be over 11
    if len(quick_replies_page_numbers_to_show) > 11:
        quick_replies_page_numbers_to_show = quick_replies_page_numbers_to_show[:11]
    for page_number in quick_replies_page_numbers_to_show:
        quick_reply = copy.deepcopy(quick_reply)
        quick_reply['title'] = "Page {}".format(page_number)
        quick_reply['url'] = "{}/news/{}/{}/{}/{}".format(
            Server_url, company, _news_type, page_number, date)
        LOG.info(quick_reply['url'])
        quick_replies.append(quick_reply)

    if quick_replies:
        message['quick_replies'] = quick_replies

    message['attachment']['payload']['elements'] = elements

    article = 'articles' if len(requested_news) > 1 else 'article'
    top_message = {"text": '{} {} {} found about {}'.
                   format(len(requested_news), news_message, article, company_net)}

    if extra_message:
        messages.append(extra_message)

    if int(page_num) == 1:
        messages.append(top_message)

    # print(message)
    messages.append(message)

    response_data = {"messages": messages}

    LOG.info(response_data)
    status = 200 if response_data is not None else 403
    js = json.dumps(response_data, indent=2)
    return flask.Response(js, status=status, mimetype='application/json')


def order_news_by_date(news):

    def comp(x, y):
        s_x = x.split('/')
        day_x = int(s_x[1]) 
        month_x = int(s_x[0]) 
        year_x = int(s_x[2])
        s_y = y.split('/')
        day_y = int(s_y[1]) 
        month_y = int(s_y[0]) 
        year_y = int(s_y[2])
        if year_x > year_y:
            return 1
        elif year_x < year_y:
            return -1
        else:
            if month_x > month_y:
                return 1
            elif month_x < month_y:
                return -1
            else:
                if day_x >= day_y:
                    return 1
                elif day_x < day_y:
                    return -1

    l = sorted(
            news,
            cmp=lambda x, y: comp(x['subtitle'], y['subtitle']),
            reverse=True
    )
    return l


@app.route(
    '/checked_article/<news_type>/<new_id>/<value>/<page_num>/<user>'.
    format(methods=['GET'])
)
def tag_article(news_type, new_id, value, page_num, user):
    """ GET Server Status API endpoint
        Args:
        Returns:
            dict: A JSON object containing the nfvacc server status information
    """

    utils.manually_tag_article(new_id, value, user)
    return get_development_news(news_type, page_num, user)


@app.route('/guest_companies'.format(methods=['GET']))
def get_companies():
    """ GET Server Status API endpoint
        Args:
        Returns:
            dict: A JSON object containing the nfvacc server status information
    """
    stocks_type = request.args.get('stocks_type')
    LOG.info(stocks_type)
    next_page = True if request.args.get('NEXT') is not None else False 
    user_id = request.args.get('chatfuel user id')
    user = mongo.find_one_match('users', {"user_id": user_id})
    if user is not None:
        if next_page:
            mongo.insert_one_in('users', {"user_id": user_id}, {
                            'companiesPage': 0})
            user = mongo.find_one_match('users', {"user_id": user_id})

        companies_page = user.get('companiesPage')
        mongo.insert_one_in('users', {"user_id": user_id}, {
                            'request': stocks_type})
        mongo.insert_one_in('users', {"user_id": user_id}, {
                            'companiesPage': companies_page+1})

    # print(user)
    # print("Fetching companies with {}.".format(stocks_type))

    attributes_dict = {"news_type": '', "stocks_type": ''}

    element = {
        "title": '',
        "image_url": '',
        "subtitle": '',
        "buttons": [{
            "type": "json_plugin_url",
            "url": '',
            "title": ''
        }]
    }
    messages = [{
        "attachment": {
            "type": "template",
            "payload": {
                "template_type": "list",
                "top_element_style": "compact",
                "elements": []
            }
        }
    }]
    next_button = {
        "type": "show_block",
        "block_name": "Next Company",
        "title": ''
    }

    if stocks_type == 'Good/Neutral News':
        companies_type = 'good_companies'
        news_type = 'positive'
        direction_list = ['POS', 'POSITIVE']

    else:
        companies_type = 'bad_companies'
        news_type = 'negative'
        direction_list = ['NEG', 'NEGATIVE']

    requested_companies = utils.companies_by_type(companies_type)
    LOG.info(len(requested_companies))
    if len(requested_companies) == 0:
        message = {"text": 'No {} where found today!'.format(stocks_type)}
        response_data = {
            'messages': [message]
        }
        status = 200 if response_data is not None else 403
        js = json.dumps(response_data, indent=2)
        return flask.Response(js, status=status, mimetype='application/json')

    requested_companies = reorder_companies(
        requested_companies, user_id, direction_list)
    four_packets = math.ceil((len(requested_companies) / 4.0))
    attributes_dict['news_type'] = news_type
    attributes_dict['stocks_type'] = stocks_type
    start = companies_page * 4
    for index, company in enumerate(requested_companies[start:]):
        if index < 4:
            element = copy.deepcopy(element)
            name_net = '+'.join((company.get('company_name')).split())
            company_name = company.get('company_name')
            element['title'] = company.get('company_name')
            element['image_url'] = str(company.get('company_logo'))
            # company_articles = utils.get_companies_articles(company_name)
            company_articles = utils.get_news_by_direction_and_company(company_name,
                                                                       direction_list, 'today')
            company_number_of_artcles = len(company_articles)
            if company_number_of_artcles == 1:
                article = company_articles[0]
                #article_title = article.get('title')[0:79]
                article_title = "1 article found about {}.".format(company_name)
            element['subtitle'] = \
                "{} articles found about {}.".format(company_number_of_artcles,
                                                   company_name)\
                if company_number_of_artcles > 1 else article_title
            element['buttons'][0][
                'title'] = 'View articles' if company_number_of_artcles > 1 else 'View article'
            element['buttons'][0][
                'url'] = '{}/company_specific/{}/{}/{}'.format(
                    Server_url, name_net, user_id, 'today')
            messages[0]['attachment']['payload']['elements'].append(
                element)

    response_data = {
        'set_attributes': attributes_dict,
        'messages': messages
    }

    if four_packets > 1:
        if (companies_page + 2) <= four_packets:
            # remaining = len(requested_companies) - (NEXT + 1) * 4
            next_button['title'] = "Next"
            response_data['messages'][0]['attachment']['payload'][
                'buttons'] = [next_button]

    if len(response_data['messages'][0]['attachment']['payload']['elements']) == 1:
        response_data['messages'][0]['attachment']['payload']['template_type'] = 'generic'
        response_data['messages'][0]['attachment']['payload'].\
            pop('top_element_style', None)
    LOG.info(response_data)
    status = 200 if response_data is not None else 403
    js = json.dumps(response_data, indent=2)
    return flask.Response(js, status=status, mimetype='application/json')


def reorder_companies(companies_list, user_id, direction_list):

    user = mongo.find_one_match('users', {"user_id": user_id})
    user_subscibed_companies = user.get('companies', None)

    sorted_list = []
    to_remove = []
    if user_subscibed_companies is not None:
        for user_company in user_subscibed_companies:
            for company in companies_list:
                if user_company == company.get('company_name'):
                    sorted_list.append(company)
                    to_remove.append(company)
                    # companies_list.remove(company)
                    break
    for comp in to_remove:
        companies_list.remove(comp)
    sorted_list.extend(companies_list)
    # sorted_list = sorted(sorted_list,
    #                      key=lambda k: len(utils.
    #                                        get_companies_articles(k['company_name'])),
    #                      reverse=True)
    sorted_list = sorted(sorted_list,
                         key=lambda k: len(utils.
                                           get_news_by_direction_and_company(k['company_name'], direction_list, 'today')),
                         reverse=True)
    return sorted_list


def signal_sigint_handler(rec_signal, rec_frame):
    os._exit(1)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_sigint_handler)
    LOG.info('scrader server started')
    # utils.news_poll(10)
    mongo.init_database()
    # utils.article_from_excel()
    # if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    #     LOG.info('main')
    #   utils.start_scheduler_task()
    # utils.update_companies_news_once()
    app.run(host='0.0.0.0', port=8000, debug=True, use_reloader=True)
