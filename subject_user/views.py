# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.generic.list_detail import object_list
from django.views.generic import list_detail
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import datetime

from profiles.models import UserProfile
from subject.models import VersionAnswer,Offset_Task, Subject
from subject_user.models import UserLesson, UserTask, UserOffset, UserTaskOffset, UserUse, UserTaskUSE, Dictionary
from subject.models import Subject, Task, VersionAnswer, Complexity, Lesson, Lesson_Task, USE, LevelTaskUse, USE_Task, Offset, Offset_Task
from mformulas.models import Formula
from configuration.models import ConfigModel
from statistics.models import StatisticsDayUser
from subject.forms import SearchForm
from project.conf import settings as conf

import urllib

#######################################################################################################################
#######################################################################################################################

def add_formula_dictionary(request, id):
	'''
		Добавление формулы в словарь
	'''
	if request.is_ajax():
		flag = True
		auser = request.user_anonymous
		
		if (auser.is_anonymous() or auser.is_not_order()) and Dictionary.objects.filter(user=request.user_anonymous).count() > ConfigModel.objects.all()[0].quantity_formulas:
			flag = False

		if flag:
			if request.method == "GET":
				if 'subject_name' in request.GET:
					subject_name = request.GET.get('subject_name')
					try:
						s = Subject.objects.get(slug=subject_name)
					except: pass
					else:
						d,create = Dictionary.objects.get_or_create(
							user = request.user_anonymous,
							subject = s,
							formula = Formula.objects.get(id=int(id))
						)
						d.set_not_mastered()

						if create:
							s,create = StatisticsDayUser.objects.get_or_create(
								user=request.user_anonymous, day=datetime.datetime.now(), subject=s
							)
							s.added_formulas += 1
							s.save()
		return HttpResponse('1')
	return HttpResponse(status=400)
	
#######################################################################################################################
#######################################################################################################################

def dictionary(request):
	'''
		Сам словарь
	'''
	if 'subject_name' in request.GET:
		subject_name = request.GET.get('subject_name')
	else:
		try: subject_name = Subject.objects.filter(is_active=True, is_olympiad=False)[0].slug
		except: raise Http404()
		else: return HttpResponseRedirect('?subject_name=%s' % subject_name)
	
	try: s = Subject.objects.get(slug=subject_name)
	except: raise Http404()
	else:
		obj_list = Dictionary.objects.filter(
			user = request.user_anonymous,
			subject = Subject.objects.get(slug=subject_name),
		)
		
		if 'is_development' in request.GET or 'is_mastered' in request.GET:
			for o in obj_list:
				if 'is_development' in request.GET:
					if not o.is_development():
						obj_list = obj_list.exclude(id=o.id)
				if 'is_mastered' in request.GET:
					if not o.is_mastered():
						obj_list = obj_list.exclude(id=o.id)
			
	return render_to_response('dictionary.html', locals(), RequestContext(request))
	
#######################################################################################################################
#######################################################################################################################



#######################################################################################################################
#######################################################################################################################

def add_lesson_bookmark(request, id):
	'''
		Добавление урока в закладку
	'''
	if request.is_ajax():
		obj,create = UserLesson.objects.get_or_create(user=request.user_anonymous, lesson=Lesson.objects.get(id=int(id)))
		obj.is_bookmark = True
		obj.save()
		return HttpResponse('1')
	return HttpResponse(status=400)
		
#######################################################################################################################
#######################################################################################################################

def bookmark(request):
	'''
		Закладки
	'''
	page = 1
	if 'page' in request.GET:
		try: page = int(request.GET.get('page'))
		except TypeError: raise Http404()
		
	obj = UserLesson.objects.filter(user=request.user_anonymous, is_bookmark=True)
	
	if 'delete' in request.GET:
		try:
			obj_d = obj.get(lesson=Lesson.objects.get(id=int(request.GET.get('delete'))))
			obj_d.is_bookmark = False
			obj_d.save()
		except: pass
		
	if 'subject_name' in request.GET:
		try:
			obj = obj.filter(lesson__subject__slug=request.GET.get('subject_name'))
		except: pass
	else: raise Http404()

	return list_detail.object_list(
		request,
		queryset = obj,
		paginate_by = conf.PAGINATE_BY,
		page = page,
		template_name = 'bookmark.html',
		template_object_name = 'obj',
		extra_context = locals(),
	)
	
#######################################################################################################################
#######################################################################################################################




#######################################################################################################################
#######################################################################################################################

def view_full_lesson(request):
	'''
		Список уроков данного класса пользователя
	'''
	if 'subject_name' in request.GET:
		subject_name = request.GET.get('subject_name')
	else:
		try: subject_name = Subject.objects.filter(is_active=True, is_olympiad=False)[0].slug
		except: raise Http404()
		else: return HttpResponseRedirect('/subjects/lesson/?subject_name=%s' % subject_name)
		
	page = 1
	if 'page' in request.GET:
		try: page = int(request.GET.get('page'))
		except TypeError: raise Http404()
		
	auser = request.user_anonymous
	if auser.get_user_in_staff():
		obj = Lesson.objects.filter(
			subject__slug=subject_name, is_active=True
		)
	else:
		obj = Lesson.objects.filter(
			subject__slug=subject_name, is_active=True, level=auser.get_level()
		)
	
	if 'is_development' in request.GET:
		obj = obj.filter(
			userlesson__is_development=True, userlesson__is_mastered=False, userlesson__user=auser
		)
	if 'is_mastered' in request.GET:
		obj = obj.filter(userlesson__is_mastered=True, userlesson__user=auser)

	if 'submit_search_form' in request.POST:
		form = SearchForm(request.POST)
		if form.is_valid():
			cd = form.cleaned_data
			if cd['title']: obj = obj.filter(title__icontains=cd['title'])
			if cd['date']: obj = obj.filter(date=cd['date'])
	else: form = SearchForm(initial={'title':_("Theme")})

	if not auser.get_user_in_staff():
		if auser.is_anonymous() or auser.is_not_order():
			free_les = ConfigModel.objects.all()[0].free_lessons
			obj = obj[:free_les]	

	return list_detail.object_list(
		request,
		queryset = obj,
		paginate_by = conf.PAGINATE_BY,
		page = page,
		template_name = 'lesson/lesson.html',
		template_object_name = 'obj',
		extra_context = locals(),
	)

#######################################################################################################################
#######################################################################################################################

def lesson_item(request, item):
	'''
		Урок и Список задач данного урока
	'''
	if 'subject_name' in request.GET:
		subject_name = request.GET.get('subject_name')
	else:
		try: subject_name = Subject.objects.filter(is_active=True, is_olympiad=False)[0].slug
		except: raise Http404()
		else: return HttpResponseRedirect('?subject_name=%s' % subject_name)
		
	auser = request.user_anonymous
	
	free_les = ConfigModel.objects.all()[0].free_lessons
	if not auser.get_user_in_staff():
		if UserLesson.objects.filter(user=request.user_anonymous, is_development=True).count() > free_les:	
			if auser.is_anonymous(): return HttpResponseRedirect('/register/')
			if auser.is_not_order(): return HttpResponseRedirect('/accounts/prolong/')
		
	l = Lesson.objects.get(slug=item, subject__slug=subject_name)
	ul, create = UserLesson.objects.get_or_create(user=request.user_anonymous, lesson=l, is_development=True)
	
	ul.repercent(request)
	
	if create:
		s,create = StatisticsDayUser.objects.get_or_create(
			user=request.user_anonymous, day=datetime.datetime.now(), subject=Subject.objects.get(slug=subject_name)
		)
		s.lessons_visited +=1
		s.save()
	
	dictionary_data = {'Lesson':[l.id]}
												
	config_lesson = {
		'autostart': False, #True or False
		'image': False, #url or False
		'start': 0, #Number
		'title': 'Title', #Text
		'description': 'description', #Text
		'controlbar': True, #True or False
		'duration': 57, #Number
		'volume': 80, #Number
		'width': 482, #Number
		'height': 300, #Number
		'events': {
			'onReady': None, #Text
			'onVolume': None, #Text
			'onError': None, #Text
			'onPlay': "onplay()", #Text
			'onPause': None, #Text
			'onSeek': None, #Text
			'onComplete': None, #Text
			'onTime': None, #Text
		}
	}
	return render_to_response('lesson/lesson_item.html', locals(), RequestContext(request))

def result_task_item(request):
	'''
		Верно ли решена задача урока
	'''
	if request.is_ajax():
		if 'subject_name' in request.GET and 'lesson_id' in request.GET and 'task_id' in request.GET:
			subject_name = request.GET.get('subject_name')
			lesson_id = int(request.GET.get('lesson_id'))
			task_id = int(request.GET.get('task_id'))
			
			try:
				s = Subject.objects.get(slug=subject_name)
				l = Lesson.objects.get(id=lesson_id)
				t = Task.objects.get(id=task_id)
			except: return HttpResponse('0')
			
			ut,create = UserTask.objects.get_or_create(user=request.user_anonymous, task=t, lesson=l)
			ut.number_attempts += 1
			
			st,create = StatisticsDayUser.objects.get_or_create(user=request.user_anonymous, day=datetime.datetime.now(), subject=s)
			st.tasks_attempts += 1
	
			if ut.task.is_true_answer(request.META['QUERY_STRING']):
				st.tasks_correct += 1
				st.save()
				
				ut.true_number_attempts += 1
				ut.is_executed = True
				ut.save()
				
				ul, create = UserLesson.objects.get_or_create(user=request.user_anonymous, lesson=l)
				ul.repercent(request)
				return HttpResponse('1')
				
			st.save()
			ut.save()
		return HttpResponse('0')
	return HttpResponse(status=400)
	
def video_on_play(request):
	'''
		Просмотр видео урока
	'''
	if request.is_ajax():
		if 'subject_name' in request.GET and 'lesson_id' in request.GET:
			subject_name = request.GET.get('subject_name')
			lesson_id = int(request.GET.get('lesson_id'))
			
			try:
				s = Subject.objects.get(slug=subject_name)
				l = Lesson.objects.get(id=lesson_id)
			except: return HttpResponse('0')
			
			ul, create = UserLesson.objects.get_or_create(user=request.user_anonymous, lesson=l, is_development=True)

			if l.video and ul.is_video_see == False:
				ul.is_video_see = True
				ul.save()
				
				ul.repercent(request)
				
			return HttpResponse('1')
		return HttpResponse('0')
	return HttpResponse(status=400)
	
#######################################################################################################################
#######################################################################################################################




#######################################################################################################################
#######################################################################################################################
	
def view_full_olympiad(request):
	'''
		Список олимпиад
	'''
	if 'subject_name' in request.GET:
		subject_name = request.GET.get('subject_name')
	else:
		try: subject_name = Subject.objects.filter(is_active=True, is_olympiad=True)[0].slug
		except: raise Http404()
		else: return HttpResponseRedirect('/olympiad/lesson/?subject_name=%s' % subject_name)
		
	page = 1
	if 'page' in request.GET:
		try: page = int(request.GET.get('page'))
		except TypeError: raise Http404()
		
	auser = request.user_anonymous
	
	if auser.get_user_in_staff():
		obj = Lesson.objects.filter(
			subject__slug=subject_name, is_active=True
		)
	else:
		obj = Lesson.objects.filter(
			subject__slug=subject_name, is_active=True, level=auser.get_level()
		)
	
	if 'is_development' in request.GET:
		obj = obj.filter(
			userlesson__is_development=True, userlesson__is_mastered=False, userlesson__user=auser
		)
	if 'is_mastered' in request.GET:
		obj = obj.filter(userlesson__is_mastered=True, userlesson__user=auser)

	if 'submit_search_form' in request.POST:
		form = SearchForm(request.POST)
		if form.is_valid():
			cd = form.cleaned_data
			if cd['title']: obj = obj.filter(title__icontains=cd['title'])
			if cd['date']: obj = obj.filter(date=cd['date'])
	else: form = SearchForm()

	return list_detail.object_list(
		request,
		queryset = obj,
		paginate_by = conf.PAGINATE_BY,
		page = page,
		template_name = 'olympiad/olympiad.html',
		template_object_name = 'obj',
		extra_context = locals(),
	)
	
#######################################################################################################################
#######################################################################################################################
	
def olympiad_item(request, item):
	'''
		Урок и Список задач олимпиады
	'''
	if 'subject_name' in request.GET:
		subject_name = request.GET.get('subject_name')
	else:
		try: subject_name = Subject.objects.filter(is_active=True, is_olympiad=True)[0].slug
		except: raise Http404()
		else: return HttpResponseRedirect('?subject_name=%s' % subject_name)
		
	l = Lesson.objects.get(slug=item, subject__slug=subject_name)
	ul, create = UserLesson.objects.get_or_create(user=request.user_anonymous, lesson=l, is_development=True)
	
	ul.repercent(request)
	
	if create:
		s,create = StatisticsDayUser.objects.get_or_create(
			user=request.user_anonymous, day=datetime.datetime.now(), subject=Subject.objects.get(slug=subject_name)
		)
		s.olympiad_visited +=1
		s.save()
	
	dictionary_data = {'Lesson':[l.id]}
												
	config_lesson = {
		'autostart': False, #True or False
		'image': False, #url or False
		'start': 0, #Number
		'title': 'Title', #Text
		'description': 'description', #Text
		'controlbar': True, #True or False
		'duration': 57, #Number
		'volume': 80, #Number
		'width': 482, #Number
		'height': 333, #Number
		'events': {
			'onReady': None, #Text
			'onVolume': None, #Text
			'onError': None, #Text
			'onPlay': "onplay()", #Text
			'onPause': None, #Text
			'onSeek': None, #Text
			'onComplete': None, #Text
			'onTime': None, #Text
		}
	}
	return render_to_response('olympiad/olympiad_item.html', locals(), RequestContext(request))
	
#######################################################################################################################
#######################################################################################################################




#######################################################################################################################
#######################################################################################################################
	
@login_required
def view_full_offset(request):
	'''
		Список зачетов пользователя (данного класса)
	'''
	if 'subject_name' in request.GET:
		subject_name = request.GET.get('subject_name')
	else:
		try: subject_name = Subject.objects.filter(is_active=True, is_olympiad=False)[0].slug
		except: raise Http404()
		else: return HttpResponseRedirect('?subject_name=%s' % subject_name)
		
	page = 1
	if 'page' in request.GET:
		try: page = int(request.GET.get('page'))
		except TypeError: raise Http404()
		
	auser = request.user_anonymous
	
	if not auser.get_user_in_staff():
		if auser.is_not_order():
			return HttpResponseRedirect('/accounts/prolong/')
	
	
	if auser.get_user_in_staff():
		obj = Offset.objects.filter(subject__slug=subject_name, is_active=True)
		for o in obj:
			UserOffset.objects.get_or_create(user=auser, offset=o)
	else:
		obj = Offset.objects.filter(subject__slug=subject_name, is_active=True, level=auser.get_level())
	

			
	if not UserOffset.objects.filter(user=auser, offset__in=obj).count():
		return render_to_response('offset/offset.html', {'obj_list':None}, RequestContext(request))

	return list_detail.object_list(
		request,
		queryset = obj,
		paginate_by = conf.PAGINATE_BY,
		page = page,
		template_name = 'offset/offset.html',
		template_object_name = 'obj',
		extra_context = locals(),
	)
	
#######################################################################################################################
#######################################################################################################################
	
@login_required
def info_offset(request):
	'''
		Информация о зачетах пользователя
	'''
	if 'subject_name' in request.GET:
		subject_name = request.GET.get('subject_name')
	else:
		try: subject_name = Subject.objects.filter(is_active=True, is_olympiad=False)[0].slug
		except: raise Http404()
		else: return HttpResponseRedirect('?subject_name=%s' % subject_name)
		
	auser = request.user_anonymous
	
	obj = UserOffset.objects.filter(
		offset__subject__slug=subject_name, offset__is_active=True, user=auser, is_executed=True
	).order_by('-date_delivery')

	return render_to_response('offset/offset_info.html', locals(), RequestContext(request))		

#######################################################################################################################
#######################################################################################################################

@login_required
def offset_item(request, item):
	'''
		Зачет
	'''
	if 'subject_name' in request.GET:
		subject_name = request.GET.get('subject_name')
	else:
		try: subject_name = Subject.objects.filter(is_active=True, is_olympiad=False)[0].slug
		except: raise Http404()
		else: return HttpResponseRedirect('?subject_name=%s' % subject_name)
		
	try: sb = Subject.objects.get(slug=subject_name)
	except: raise Http404('sb not exist')
		
	auser = request.user_anonymous
	
	if not auser.get_user_in_staff():
		if auser.is_not_order():
			return HttpResponseRedirect('/accounts/prolong/')
	
	next = 0
	if auser.get_user_in_staff():
		try: obj = Offset.objects.get(slug=item, subject__slug=subject_name, is_active=True)
		except: raise Http404('obj not exist')
	else:
		try: obj = Offset.objects.get(slug=item, subject__slug=subject_name, is_active=True, level=auser.get_level())
		except: raise Http404('obj not exist')
	
	try: offs = UserOffset.objects.get(user=auser, offset=obj)
	except: return render_to_response('offset/offset.html', {'obj_list':None}, RequestContext(request))
	
	date_end = offs.date_delivery + datetime.timedelta(hours=int(obj.time.hour), minutes=int(obj.time.minute), seconds=int(obj.time.second))
	
	tasks = obj.get_task_list()

	if 'next' in request.GET:
		next = request.GET.get('next')
		if next == 'start':
			offs.is_executed = False
			offs.number_attempts += 1
			offs.date_delivery = datetime.datetime.now()
			offs.save()
			
			s,create = StatisticsDayUser.objects.get_or_create(
				user=auser, day=datetime.datetime.now(), subject=sb
			)
			s.offsets_attempts += 1
			s.save()
					
			UserTaskOffset.objects.filter(user_task_offset=offs).delete()
		
			return HttpResponseRedirect('?next=0&subject_name=%s'% subject_name)
			
		elif next == 'end':
			end = True
			
		elif next == 'timeout':
			timeout = True
			
		else:
			try: next = int(next)
			except TypeError: raise Http404('next != [0-9]+')
				
			if next >= 0:
				#Проверка времени
				if datetime.datetime.now() > date_end:
					return HttpResponseRedirect('?next=timeout&subject_name=%s'% subject_name)
				
				if next > 0:
					obj_list = tasks[next-1]
					if 'answerr' in request.GET:
						#Записали ответ пользователя
						tas, create = UserTaskOffset.objects.get_or_create(
							task=obj_list, user_task_offset=offs
						)
						
						# Проверка ответов
						tas.number_attempts += 1
						tas.answer = urllib.unquote(request.META['QUERY_STRING'])
						if tas.task.is_true_answer(urllib.unquote(request.META['QUERY_STRING'])):
							tas.is_executed = True
							tas.true_number_attempts += 1
						tas.save()
					
				if next > tasks.count() - 1:
					# Проверили сдан ли зачет
					if offs.offset_is_executed():					
						offs.true_number_attempts += 1
						offs.is_executed = True
						offs.save()
						
						s,create = StatisticsDayUser.objects.get_or_create(
							user=auser, day=datetime.datetime.now(), subject=sb
						)
						s.offsets_correct += 1
						s.save()
					return HttpResponseRedirect('?next=end&subject_name=%s'% subject_name)

				obj_list = tasks[next]
				next = next + 1
			else: raise Http404('next < 0')
		
	return render_to_response('offset/offset_item.html', locals(), RequestContext(request))
	
#######################################################################################################################
#######################################################################################################################

@login_required	
def result_offset_item(request, item):
	'''
		Результаты зачета
	'''
	if 'subject_name' in request.GET:
		subject_name = request.GET.get('subject_name')
	else:
		try: subject_name = Subject.objects.filter(is_active=True, is_olympiad=False)[0].slug
		except: raise Http404()
		else: return HttpResponseRedirect('?subject_name=%s' % subject_name)
		
	try: obj = Offset.objects.get(slug=item, subject__slug=subject_name)
	except: raise Http404()
	
	auser = request.user_anonymous
	
	if not auser.get_user_in_staff():
		if auser.is_not_order():
			return HttpResponseRedirect('/accounts/prolong/')
	
	#перешли в новый класс
	offsets_executed = UserOffset.objects.filter(user=auser, offset__level=auser.get_level(), is_executed=True).count()
	all_offsets = Offset.objects.filter(is_active=True, level=auser.get_level()).count()
	
	if not auser.is_anonymous():
		if offsets_executed >= all_offsets and offsets_executed > 0 and all_offsets > 0:
			up = auser.user.get_profile()
			up.level += 1
			up.save()
			
			new_class = True
	
	return render_to_response('offset/offset_result.html', locals(), RequestContext(request))

#######################################################################################################################
#######################################################################################################################




#######################################################################################################################
#######################################################################################################################	

def view_full_use(request):
	'''
		Список ЕГЭ
	'''
	if 'subject_name' in request.GET:
		subject_name = request.GET.get('subject_name')
	else:
		try: subject_name = Subject.objects.filter(is_active=True, is_olympiad=False)[0].slug
		except: raise Http404()
		else: return HttpResponseRedirect('?subject_name=%s' % subject_name)
		
	page = 1
	if 'page' in request.GET:
		try: page = int(request.GET.get('page'))
		except TypeError: raise Http404()
		
	auser = request.user_anonymous
	
	obj = USE.objects.filter(is_active=True, subject__slug=subject_name)
	
	if 'is_executed' in request.GET:
		obj = obj.filter(plus_users__is_executed=True, plus_users__user=auser)
	
	return list_detail.object_list(
		request,
		queryset = obj,
		paginate_by = conf.PAGINATE_BY,
		page = page,
		template_name = 'use/use.html',
		template_object_name = 'obj',
		extra_context = locals(),
	)
	
#######################################################################################################################
#######################################################################################################################	

def use_item(request, item, next=0):
	if 'subject_name' in request.GET:
		subject_name = request.GET.get('subject_name')
	else:
		try: subject_name = Subject.objects.filter(is_active=True, is_olympiad=False)[0].slug
		except: raise Http404()
		else: return HttpResponseRedirect('?subject_name=%s' % subject_name)
		
	try: sb = Subject.objects.get(slug=subject_name)
	except: raise Http404('sb not exist')
	
	auser = request.user_anonymous
	
	next = 0
	
	try: obj = USE.objects.get(slug=item, subject__slug=subject_name)
	except: raise Http404()
	
	uu, create = UserUse.objects.get_or_create(user=auser, use=obj)
	
	date_end = uu.date_delivery + datetime.timedelta(hours=int(obj.time.hour), minutes=int(obj.time.minute), seconds=int(obj.time.second))
	
	tasks = obj.get_task_list()
	usetasks = USE_Task.objects.filter(USE=uu.use).order_by('level_task_use')
	
	if 'next' in request.GET:
		next = request.GET.get('next')
		
		if next == 'start':
			#Начать егэ
			UserTaskUSE.objects.filter(user_use=uu).delete()
			
			uu.date_delivery = datetime.datetime.now()
			uu.is_executed = False
			uu.true_number_attempts = 0
			uu.number_attempts += 1
			uu.points = 0
			uu.save()
			
			for i in tasks:
				tas, create = UserTaskUSE.objects.get_or_create(
							task=i, user_use=uu
						)
			
			# статистика
			s,create = StatisticsDayUser.objects.get_or_create(
				user=auser, day=datetime.datetime.now(), subject=sb
			)
			s.use_attempts += 1
			s.save()
			
			return HttpResponseRedirect('?next=0&subject_name=%s'% (subject_name))
			
		elif next == 'end':
			#кнопка закончить егэ
			end = True
			
		elif next == 'timeout':
			#Время вышло
			timeout = True
			
		else:
			try: next = int(next)
			except TypeError: raise Http404('next != [0-9]+')
			
			if next >= 0:
				#Проверка времени
				if datetime.datetime.now() > date_end:
					return HttpResponseRedirect('?next=timeout&subject_name=%s'% subject_name)
				
				if next > 0:
					obj_list = tasks[next-1]
					if 'answerr' in request.GET:
						#Записали ответ пользователя
						tas, create = UserTaskUSE.objects.get_or_create(
							task=obj_list, user_use=uu
						)
						
						# Проверка ответов
						tas.number_attempts += 1
						tas.answer = urllib.unquote(request.META['QUERY_STRING'])
						if tas.task.is_true_answer(request.META['QUERY_STRING']):
							tas.is_executed = True
							tas.true_number_attempts += 1
						else:
							tas.is_executed = False
							
							# uu.points += tas.task.for_use_task_task.filter(USE=uu.use)[0].quantity_point
							# uu.save()
						tas.save()
					
				if next > tasks.count() - 1:
					# Завершить ЕГЭ
					#Считаем баллы:
					point = 0
					all_uu = UserTaskUSE.objects.filter(user_use = uu,is_executed = True)
					for us in all_uu:
						point += us.task.for_use_task_task.filter(USE=uu.use)[0].quantity_point
					uu.points = point
					uu.save()
					#Посчитали
					if uu.use_is_executed():
						uu.true_number_attempts += 1
						uu.is_executed = True
						uu.save()
					
					s,create = StatisticsDayUser.objects.get_or_create(
						user=auser, day=datetime.datetime.now(), subject=sb
					)
					s.use_correct += 1
					s.save()
					return HttpResponseRedirect('?next=end&subject_name=%s'% subject_name)

				obj_list = tasks[next]
				next = next + 1
			else: raise Http404('next < 0')

	return render_to_response('use/use_item.html', locals(), RequestContext(request))
	
#######################################################################################################################
#######################################################################################################################	

def result_use_item(request, item,):
	'''
		Результат пройденного ЕГЭ
	'''
	if 'subject_name' in request.GET:
		subject_name = request.GET.get('subject_name')
	else:
		try: subject_name = Subject.objects.filter(is_active=True, is_olympiad=False)[0].slug
		except: raise Http404()
		else: return HttpResponseRedirect('?subject_name=%s' % subject_name)
		
	auser = request.user_anonymous
	
	try: obj = USE.objects.get(slug=item, subject__slug=subject_name)
	except: raise Http404()
	
	try: uu = UserUse.objects.get(user=auser, use=obj)
	except: raise Http404()
	
	tasks = obj.get_task_list()
	usetasks = UserTaskUSE.objects.filter(user_use=uu).order_by('id')
	
	return render_to_response('use/use_result.html', locals(), RequestContext(request))
	
#######################################################################################################################
#######################################################################################################################	