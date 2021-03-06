# -*- coding:utf-8 -*-
import time
import urllib
import json
import re

from app.controller import verify
from app.models import Task
from twitter import error
from flask import request, render_template, jsonify, redirect, url_for

from crawler.basicinfo_crawler import BasicinfoCrawler
from crawler.relation_crawler import RelationCrawler
from crawler.tweets_crawler import TweetsCrawler

basicinfo_crawler = BasicinfoCrawler()
relation_crawler = RelationCrawler()
tweets_crawler = TweetsCrawler()


'''
返回用户查询页面
'''
@verify
def user_search():
	return render_template('user_search.html')


'''
返回两个用户的关系
'''
@verify
def get_user_relation():
	screen_name1 = request.form['screen_name1'].strip()
	screen_name2 = request.form['screen_name2'].strip()
	
	try:
		rel = relation_crawler.show_friendship(source_screen_name = screen_name1, target_screen_name = screen_name2)
	except error.TwitterError as te:
		try:
			status = None
			if te.message[0]['code'] == 88:
				status = "ratelimit"

			elif te.message[0]['code'] == 63:
				status = "suspend"

			elif te.message[0]['code'] == 50:
				status = "notfound"

			return jsonify(status)
		except Exception as ee:
			return jsonify(None)
	except Exception as e:
		return jsonify(None)

	res = {
		'source': {
			"id_str": rel['relationship']['source']['id_str'],
			"screen_name": rel['relationship']['source']['screen_name'],
			"followed_by": rel['relationship']['source']['followed_by'],
			"following": rel['relationship']['source']['following']
		},
		'target': {
			"id_str": rel['relationship']['target']['id_str'],
			"screen_name": rel['relationship']['target']['screen_name'],
			"followed_by": rel['relationship']['target']['followed_by'],
			"following": rel['relationship']['target']['following']
		}
	}
	
	return jsonify(res)


'''
返回用户推文
'''
@verify
def get_user_tweets():
	screen_name = request.form['screen_name']
	max_id = request.form['max_id']
	count = 30

	if max_id == '0':
		max_id = 1

	max_id = long(max_id) - 1

	try:
		tweets = tweets_crawler.get_user_timeline(screen_name = screen_name, max_id = max_id, count = count)
	except error.TwitterError as te:
		try:
			status = None
			if te.message[0]['code'] == 88:
				status = "ratelimit"

			elif te.message[0]['code'] == 63:
				status = "suspend"

			elif te.message[0]['code'] == 50:
				status = "notfound"

			return jsonify(status)
		except Exception as ee:
			return jsonify(None)
	except Exception as e:
		return jsonify(None)

	res = []
	for tweet in tweets:
		res.append({
			'id': tweet.id,
			'text':len(tweet.text) > 48 and tweet.text[0 : 48] + " ..." or tweet.text,
			'created_at':time.strftime('%Y-%m-%d', time.strptime(tweet.created_at.replace('+0000 ',''))),
			'favorite_count':tweet.favorite_count,
			'retweet_count':tweet.retweet_count,
			'lang':tweet.lang,
			'source':re.sub(r'^<a href.+?>','',tweet.source)[0 : -4]
		})
		
	return jsonify(res)


'''
获取用户朋友
'''
@verify
def get_user_friends():
	screen_name = request.form['screen_name']
	cursor = request.form['cursor']
	count = 30

	if cursor == None:
		cursor = -1

	cursor = long(cursor)

	try:
		friends = relation_crawler.get_friends_paged(screen_name = screen_name, cursor = cursor, count = count)
	except error.TwitterError as te:
		try:
			status = None
			if te.message[0]['code'] == 88:
				status = "ratelimit"

			elif te.message[0]['code'] == 63:
				status = "suspend"

			elif te.message[0]['code'] == 50:
				status = "notfound"

			return jsonify(status)
		except Exception as ee:
			return jsonify(None)
	except Exception as e:
		return jsonify(None)

	res = []
	for friend in friends[2]:
		res.append({
			'screen_name':friend.screen_name,
			'name':friend.name,
			'created_at':time.strftime('%Y-%m-%d', time.strptime(friend.created_at.replace('+0000 ',''))),
			'friends_count':friend.friends_count,
			'followers_count':friend.followers_count,
			'status_count':friend.statuses_count,
			'lang':friend.lang,
			'description':len(friend.description) > 48 and friend.description[0 : 48] + " ..." or friend.description,
		})
		
	return jsonify([friends[0], res])


'''
获取用户粉丝
'''
@verify
def get_user_followers():
	screen_name = request.form['screen_name']
	cursor = request.form['cursor']
	count = 30

	if cursor == None:
		cursor = -1

	cursor = long(cursor)

	try:
		followers = relation_crawler.get_followers_paged(screen_name = screen_name, cursor = cursor, count = count)
	except error.TwitterError as te:
		try:
			status = None
			if te.message[0]['code'] == 88:
				status = "ratelimit"

			elif te.message[0]['code'] == 63:
				status = "suspend"

			elif te.message[0]['code'] == 50:
				status = "notfound"

			return jsonify(status)
		except Exception as ee:
			return jsonify(None)
	except Exception as e:
		return jsonify(None)

	res = []

	for follower in followers[2]:
		res.append({
			'screen_name':follower.screen_name,
			'name':follower.name,
			'created_at':time.strftime('%Y-%m-%d', time.strptime(follower.created_at.replace('+0000 ',''))),
			'friends_count':follower.friends_count,
			'followers_count':follower.followers_count,
			'status_count':follower.statuses_count,
			'lang':follower.lang,
			'description':len(follower.description) > 48 and follower.description[0 : 48] + " ..." or follower.description,
		})
		
	return jsonify([followers[0], res])


'''
返回用户信息（基础信息、部分关系信息、部分推文信息）页面
'''
@verify
def user_profile(screen_name):
	status = 0

	try:
		user = basicinfo_crawler.get_user(screen_name = screen_name)

	except error.TwitterError as te:
		try:
			if te.message[0]['code'] == 88:
				status = "ratelimit"

			elif te.message[0]['code'] == 63:
				status = "suspend"

			elif te.message[0]['code'] == 50:
				status = "notfound"
		except Exception as ee:
			status = 0

		return render_template('user_profile.html', status = status, user = None, followers = [], friends = [], tweets = [])
	except:
		status = 0
		return render_template('user_profile.html', status = status, user = None, followers = [], friends = [], tweets = [])

	friends = []
	followers = []
	res = []

	try:
		friends = relation_crawler.get_friends(screen_name = screen_name, total_count = 30)
		for friend in friends:
			friend.created_at = time.strftime('%Y-%m-%d', time.strptime(friend.created_at.replace('+0000 ','')))
			if len(friend.description) > 28:
				friend.description = friend.description[0:28]
				friend.description += ' ...'

	except Exception as te:
		pass

	try:
		followers = relation_crawler.get_followers(screen_name = screen_name, total_count = 30)
		for follower in followers:
			follower.created_at = time.strftime('%Y-%m-%d', time.strptime(follower.created_at.replace('+0000 ','')))
			if len(follower.description) > 8:
				follower.description = follower.description[0:18]
				follower.description += ' ...'

	except Exception as te:
		pass

	try:
		tweets = tweets_crawler.get_user_timeline(screen_name = screen_name, count = 30)

		for tweet in tweets:
			res.append({
				# 'id': tweet.id,
				'text':len(tweet.text) > 48 and tweet.text[0 : 48] + " ..." or tweet.text,
				'created_at':time.strftime('%Y-%m-%d', time.strptime(tweet.created_at.replace('+0000 ',''))),
				'favorite_count':tweet.favorite_count,
				'retweet_count':tweet.retweet_count,
				'lang':tweet.lang,
				'source':re.sub(r'^<a href.+?>','',tweet.source)[0 : -4]
			})

	except Exception as te:
		pass

	user.created_at = time.strftime('%Y-%m-%d', time.strptime(user.created_at.replace('+0000 ','')))

	get_image(user.profile_image_url, screen_name)

	return render_template('user_profile.html', status = 1, user = user, followers = followers, friends = friends, tweets = res)


'''
根据url下载图片
'''
def get_image(url, screen_name):
	urllib.urlretrieve(url.replace('normal.','bigger.'), 'app/static/profile/%s.jpg' % screen_name)


'''
返回根据关键词查询用户的结果
'''
@verify
def user_search_detail():
	data = json.loads(request.form['aoData'])

	for item in data:
		if item['name'] == 'sSearch':
			s_search = item['value']
			break

		if item['name'] == 'iDisplayLength':
			data_length = item['value']

	if s_search == '':
		return jsonify({'aaData': []})

	data_length  = int(data_length)
	if data_length > 100:
		data_length = 100

	page = 1
	flag = True
	count = data_length / 20
	user_list = []

	try:
		while count > 0:
			user_temp = basicinfo_crawler.get_users_search(term = s_search, count = 20, page = page)
			user_list.extend(user_temp)
			page += 1

			if len(user_temp) < 20:
				flag = False
				break

			count -= 1

		if data_length % 20 != 0 and flag:	
			user_list.extend(basicinfo_crawler.get_users_search(term = s_search, page = page, count = data_length % 20))

	except:
		return jsonify({'aaData': []})

	res = []
	for user in user_list:
		if user.description != '':
			description = len(user.description) < 28 and user.description or user.description[0 : 28] + " ..."
		else :
			description = ''

		res.append({
			'screen_name': user.screen_name,
			'name': user.name,
			'created_at': time.strftime('%Y-%m-%d %H:%M:%S', time.strptime(user.created_at.replace('+0000 ',''))),
			'description': description,
			'followers_count': user.followers_count,
			'friends_count': user.friends_count,
			'statuses_count': user.statuses_count,
			'lang': user.lang
		})

	return jsonify({'aaData': res})


'''
返回用户关系查询页面
'''
@verify
def relation_search():
	return render_template('relation_search.html')


'''
返回用户推文查询页面
'''
@verify
def tweets_search():
	return render_template('tweets_search.html')