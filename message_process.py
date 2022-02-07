import sqlite3
import datetime
from datetime import date, timedelta, datetime
import numpy
import time
import matplotlib.pyplot as plt
import matplotlib.dates
import matplotlib.patches as mpatches
import pandas as pd
#from pandas.table.plotting import table
from pandas.plotting import table
import dataframe_image as dfi
from io import BytesIO
import win32clipboard
from PIL import Image
import random

def send_to_clipboard(image):
    output = BytesIO()
    image.convert('RGB').save(output, 'BMP')
    data = output.getvalue()[14:]
    output.close()

    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    win32clipboard.CloseClipboard()

def addActivityPointsForTheDay(cur, conn, user_id, date_, activity_points):

    cur.execute('SELECT user_id FROM USER WHERE user_id = ?', (user_id,))
    result = cur.fetchall()

    if len(result) == 0:
        print("No such user exists")

    else:
        cur.execute('SELECT date_ FROM POINTS WHERE date_ = ? AND user_id = ?', (date_, user_id))
        result = cur.fetchall()

        if len(result) == 0:
            cur.execute('INSERT INTO POINTS VALUES (?,?,?,?)', (user_id, date_, 0, activity_points))
        else:
            cur.execute(
                'UPDATE POINTS SET activity_points = (activity_points + ?) WHERE date_ = ? AND user_id = ?',
                (activity_points, date_, user_id))

    #conn.commit()

def addFollowUpPointsForTheDay(cur, conn, user_id, date_, follow_up_points):
    cur.execute('SELECT user_id FROM USER WHERE user_id = ?', (user_id,))
    result = cur.fetchall()

    if len(result) == 0:
        print("No such user exists")


    else:
        cur.execute('SELECT date_ FROM POINTS WHERE date_ = ? AND user_id = ?', (date_, user_id))
        result = cur.fetchall()

        if len(result) == 0:
            cur.execute('INSERT INTO POINTS VALUES (?,?,?,?)', (user_id, date_, follow_up_points, 0))
        else:
            cur.execute(
                'UPDATE POINTS SET follow_up_points = (follow_up_points + ?) WHERE date_ = ? AND user_id = ?',
                (follow_up_points, date_, user_id))

    #conn.commit()

def repetition_in_book(cur, conn, external_link):
    hasError = False
    temparr = external_link.split('|')
    book_id = int(temparr[0])
    arr = temparr[1].split(",")
    cur.execute('SELECT book_id FROM BOOK WHERE book_id = ?', (book_id,))
    result = cur.fetchall()
    if len(result) == 0:
        hasError = True
        return hasError, -1 # -1 as a flag if no such book exists

    rep = 0
    list = []
    for i in range(len(arr)):
        arr2 = arr[i].split("-")
        list.append(arr2)
        # [ [1,10], [13,15], [18] ]
    for i in range(len(list)):
        if len(list[i]) == 1:
            try:
                pg = int(list[i][0])
                if not hasError:
                    rep += 1
            except:
                hasError = True

        elif len(list[i]) == 2:
            try:
                pgstart = int(list[i][0])
                pgend = int(list[i][1])
                if pgstart <= pgend:
                    for j in range(pgstart, pgend + 1):
                        if not hasError:
                            rep += 1
            except:
                hasError = True
        else:
            hasError = True

    return hasError, rep



def process_response(cur, conn, user_name, user_id, wt_msg, command):
    print('Got', user_name, user_id, wt_msg, command )
    send_to = None # 0 - personal chat, 1 - group
    response_type = None # 0 - text, 1- image
    file_location = None # if reply is an image
    response_msg = None # if reply is a text

    if(command!=None):
        if(command == 'available_books'):
            cur.execute('SELECT * FROM BOOK')
            book_list = cur.fetchall()

            # convert to pandas dataframe, create as image for this dats
            df = pd.DataFrame(book_list, columns=['Book_ID','Book Name'])
            n,m = df.shape
            ax = plt.subplot(n,m,(1,10), frame_on=False) # no visible frame
            ax.xaxis.set_visible(False)  # hide the x axis
            ax.yaxis.set_visible(False)  # hide the y axis
            table(ax, df)

            # save that image
            now = datetime.now()
            file_name = (now.strftime("%d_%m_%Y_%H_%M_%S")) + '.png'
            file_location = 'user_data//' + command + '//' + file_name
            plt.savefig(file_location)
            plt.clf()
            plt.cla()
            plt.close()
            send_to = 0
            response_type = 1

        if(command == 'hourly_report'):
            send_to = 1
            response_type = 1

            now = datetime.now()
            date_ = now.strftime("%Y-%m-%d")
            total_pts = 0
            points_list = []
            hour_list = []

            for start_hr in range(0, 24):
                end_hr = start_hr + 1
                start_time = str(date_) + ' ' + str(start_hr) + ':00:00'
                end_time = str(date_) + ' ' + str(end_hr) + ':00:00'
                if start_hr < 10:
                    start_time = str(date_) + ' 0' + str(start_hr) + ':00:00'
                if end_hr < 10:
                    end_time = str(date_) + ' 0' + str(end_hr) + ':00:00'
                cur.execute(
                    'SELECT a.date_time_completed,l.activity_name,l.points,a.repetition FROM ACTIVITIES_DONE a, '
                    'LIST_OF_ACTIVITIES l WHERE a.date_time_completed>= ? AND a.date_time_completed< ? AND '
                    'a.activity_id = l.activity_id AND a.user_id= ? ORDER BY a.date_time_completed',
                    (start_time, end_time, user_id))
                sub_total = 0
                result1 = cur.fetchall()
                flag = 0

                for j in result1:
                    temp = int(j[2]) * int(j[3])
                    sub_total += temp
                    total_pts += temp

                points_list.append(sub_total)
                hour_list.append(start_hr + 0.5)

            cur.execute('SELECT follow_up_points, activity_points FROM POINTS WHERE user_id = ? AND date_ = ?',(user_id,date_))
            result = cur.fetchall()
            if(len(result)==0):
                act_pt = 0
                fol_pt = 0
            else:
                act_pt = int(result[0][1])
                fol_pt = int(result[0][0])

            cur.execute('SELECT pts_fetched FROM wake_up_time WHERE user_id = ? AND date_ = ?',(user_id,date_))
            result = cur.fetchall()
            if(len(result)==0):
                wake_pt = 0
            else:
                wake_pt = int(result[0][0])

            total_pt = act_pt + fol_pt
            act_pt -= wake_pt

            act = 'ACT_PTS-'+str(act_pt)
            fol = 'FOL_PTS-'+str(fol_pt)
            wak = 'WAKE_PT-'+str(wake_pt)


            plt.plot(hour_list, points_list, color='blue', marker='o', markerfacecolor='blue', markersize=9)
            plt.xlabel('Hour - axis')
            plt.ylabel('Points - axis')
            total_pts_str = 'Total Points on [' + date_ + '] - ' + str(total_pt) + ' points (' + user_name +')'
            #plt.figtext(.4, .9, total_pts_str)
            plt.title(total_pts_str)

            red_path = mpatches.Patch(color='red',label=act)
            green_path = mpatches.Patch(color='green',label=fol)
            blue_path = mpatches.Patch(color='blue',label=wak)
            plt.legend(handles=[red_path,green_path,blue_path])

            # save that image
            now = datetime.now()
            file_name = (now.strftime("%d_%m_%Y_%H_%M_%S")) + '.png'
            file_location = 'user_data//' + command + '//' + file_name
            plt.savefig(file_location)
            plt.clf()
            plt.cla()
            plt.close()

        if(command == 'leaderboard'):
            cur.execute('''SELECT u.user_name,p.date_,p.follow_up_points,
            p.activity_points,sum(p.follow_up_points+p.activity_points) as tot
            FROM points p, user u WHERE u.user_id = p.user_id
            GROUP BY p.user_id,p.date_ ORDER BY tot DESC;''')
            rank_result = cur.fetchall()
            # convert to pandas dataframe, create as image for this dats
            df = pd.DataFrame(rank_result, columns=['USER NAME','DATE','FOLLOW UP POINTS','ACTIVITY POINTS','TOTAL POINTS'])
            n,m = df.shape
            ax = plt.subplot(n,m,(1,10), frame_on=False)
            ax.xaxis.set_visible(False)  # hide the x axis
            ax.yaxis.set_visible(False)  # hide the y axis
            table(ax, df.head(10))

            # save that image
            now = datetime.now()
            file_name = (now.strftime("%d_%m_%Y_%H_%M_%S")) + '.png'
            file_location = 'user_data//' + command + '//' + file_name
            plt.savefig(file_location)
            plt.clf()
            plt.cla()
            plt.close()
            send_to = 1
            response_type = 1

        if(command == 'book_follow_up'):
            send_to = 0
            response_type = 0

            today = datetime.now().strftime("%Y-%m-%d")
            cur.execute(
                'SELECT a.book_id,a.activity_register,f.next_follow_up_number_id,count(a.page_no) FROM FOLLOW_UP f, BOOK_READ_REGISTER a WHERE f.date_to_be_done '
                '<= ? AND f.date_time_completed IS NULL AND a.activity_register=f.activity_register  '
                'AND f.activity_register IN (SELECT activity_register FROM ACTIVITIES_DONE WHERE user_id = ? AND activity_id = 25) GROUP BY a.activity_register ORDER BY f.date_to_be_done',
                (today, user_id))
            result = cur.fetchall()

            if(len(result)==0):
                response_msg = 'You have no follow ups. Everything up to date'
            else:
                response_msg = ''
                no_of_fup_to_return = 2
                index = 0
                while(index<len(result) and index<no_of_fup_to_return):
                    book_id = int(result[index][0])
                    activity_register = int(result[index][1])
                    follow_up_number = int(result[index][2])
                    date_ = str(today)

                    cur.execute(
                        'SELECT activity_register FROM FOLLOW_UP WHERE activity_register = ? AND next_follow_up_number_id '
                        '= ? AND date_time_completed IS NULL', (activity_register, follow_up_number))
                    result_2 = cur.fetchall()

                    if len(result_2) == 0:
                        response_msg = 'Something went wrong you have already completed this book follow up'
                    else:
                        cur.execute(
                            'UPDATE FOLLOW_UP SET date_time_completed =? WHERE activity_register = ? AND date_time_completed IS NULL AND next_follow_up_number_id=?;',
                            (date_, activity_register, follow_up_number))
                        cur.execute('SELECT days_to_be_added FROM FOLLOW_UP_NUMBER WHERE follow_up_number_id = ?',
                                    (follow_up_number,))
                        result_3 = cur.fetchall()

                        date_str = date_
                        date_object = datetime.strptime(date_str, '%Y-%m-%d').date()
                        date_object = date_object + timedelta(days=int(result_3[0][0]))
                        date_str = date_object.strftime("%Y-%m-%d")

                        if follow_up_number <= 6:
                            follow_up_number += 1
                        else:
                            follow_up_number = 7
                        cur.execute(
                            'INSERT INTO FOLLOW_UP(activity_register,date_to_be_done,next_follow_up_number_id) VALUES (?,?,?)',
                            (activity_register, date_str, follow_up_number))

                        cur.execute('SELECT points FROM LIST_OF_ACTIVITIES WHERE activity_id = 25')
                        pts = cur.fetchall()
                        cur.execute('SELECT repetition FROM ACTIVITIES_DONE WHERE activity_register = ?;',
                                    (activity_register,))
                        rep = cur.fetchall()

                        follow_up_points = int(0.5 * float(pts[0][0]) * float(rep[0][0]))

                        addFollowUpPointsForTheDay(cur, conn, user_id, date_, follow_up_points)
                        #conn.commit()

                        response_msg += (str(book_id) + ' - ')
                        cur.execute('SELECT page_no FROM BOOK_READ_REGISTER WHERE activity_register = ?', (activity_register,))
                        pages = cur.fetchall()

                        page_str = ''
                        for j in pages:
                            page_str = page_str + str(j[0]) + ','
                        page_str = page_str[0:len(page_str) - 1]
                        response_msg += (page_str + '\n')
                        index += 1
            #conn.commit()

        if(command == 'word_follow_up'):
            send_to = 0
            response_type = 0

            today = datetime.now().strftime("%Y-%m-%d")
            cur.execute(
                'SELECT a.word,a.activity_register,f.next_follow_up_number_id,a.meaning FROM FOLLOW_UP f, VOCABULARY a WHERE f.date_to_be_done '
                '<= ? AND f.date_time_completed IS NULL AND a.activity_register=f.activity_register  '
                'AND f.activity_register IN (SELECT activity_register FROM ACTIVITIES_DONE WHERE user_id = ? AND activity_id = 27) ORDER BY f.date_to_be_done',
                (today, user_id))
            result = cur.fetchall()

            if(len(result)==0):
                response_msg = 'You have no follow ups. Everything up to date'
            else:
                response_msg = ''
                no_of_fup_to_return = 5
                index = 0
                while(index<len(result) and index<no_of_fup_to_return):
                    word = str(result[index][0])
                    activity_register = int(result[index][1])
                    follow_up_number = int(result[index][2])
                    meaning = str(result[index][3])
                    date_ = str(today)

                    cur.execute(
                        'SELECT activity_register FROM FOLLOW_UP WHERE activity_register = ? AND next_follow_up_number_id '
                        '= ? AND date_time_completed IS NULL', (activity_register, follow_up_number))
                    result_2 = cur.fetchall()

                    if len(result_2) == 0:
                        response_msg = 'Something went wrong you have already completed this word follow up'
                    else:
                        cur.execute(
                            'UPDATE FOLLOW_UP SET date_time_completed =? WHERE activity_register = ? AND date_time_completed IS NULL AND next_follow_up_number_id=?;',
                            (date_, activity_register, follow_up_number))
                        cur.execute('SELECT days_to_be_added FROM FOLLOW_UP_NUMBER WHERE follow_up_number_id = ?',
                                    (follow_up_number,))
                        result_2 = cur.fetchall()

                        date_str = date_
                        date_object = datetime.strptime(date_str, '%Y-%m-%d').date()
                        date_object = date_object + timedelta(days=int(result_2[0][0]))
                        date_str = date_object.strftime("%Y-%m-%d")

                        if follow_up_number <= 6:
                            follow_up_number += 1
                        else:
                            follow_up_number = 7
                        cur.execute(
                            'INSERT INTO FOLLOW_UP(activity_register,date_to_be_done,next_follow_up_number_id) VALUES (?,?,?)',
                            (activity_register, date_str, follow_up_number))

                        cur.execute('SELECT points FROM LIST_OF_ACTIVITIES WHERE activity_id = 27')
                        pts = cur.fetchall()
                        cur.execute('SELECT repetition FROM ACTIVITIES_DONE WHERE activity_register = ?;',
                                    (activity_register,))
                        rep = cur.fetchall()

                        follow_up_points = int(0.5 * float(pts[0][0]) * float(rep[0][0]))

                        addFollowUpPointsForTheDay(cur, conn, user_id, date_, follow_up_points)
                        #conn.commit()

                        response_msg += (word + ' - ' + meaning + '\n')
                        index += 1
            #conn.commit()

        if(command == 'article_follow_up'):
            send_to = 0
            response_type = 0

            today = datetime.now().strftime("%Y-%m-%d")
            cur.execute(
                'SELECT a.article_link,a.activity_register,f.next_follow_up_number_id FROM FOLLOW_UP f, ARTICLES a WHERE f.date_to_be_done '
                '<= ? AND f.date_time_completed IS NULL AND a.activity_register=f.activity_register  '
                'AND f.activity_register IN (SELECT activity_register FROM ACTIVITIES_DONE WHERE user_id = ? AND activity_id = 26) ORDER BY f.date_to_be_done',
                (today, user_id))
            result = cur.fetchall()

            if(len(result)==0):
                response_msg = 'You have no follow ups. Everything up to date'
            else:
                response_msg = ''
                no_of_fup_to_return = 2
                index = 0
                while(index<len(result) and index<no_of_fup_to_return):
                    article_link = result[index][0]
                    activity_register = int(result[index][1])
                    follow_up_number = int(result[index][2])
                    date_ = str(today)

                    cur.execute(
                        'SELECT activity_register FROM FOLLOW_UP WHERE activity_register = ? AND next_follow_up_number_id '
                        '= ? AND date_time_completed IS NULL', (activity_register, follow_up_number))
                    result_2 = cur.fetchall()

                    if len(result_2) == 0:
                        response_msg = 'Something went wrong you have already completed this article follow up'
                    else:
                        cur.execute(
                            'UPDATE FOLLOW_UP SET date_time_completed =? WHERE activity_register = ? AND date_time_completed IS NULL AND next_follow_up_number_id=?;',
                            (date_, activity_register, follow_up_number))
                        cur.execute('SELECT days_to_be_added FROM FOLLOW_UP_NUMBER WHERE follow_up_number_id = ?',
                                    (follow_up_number,))
                        result_3 = cur.fetchall()

                        date_str = date_
                        date_object = datetime.strptime(date_str, '%Y-%m-%d').date()
                        date_object = date_object + timedelta(days=int(result_3[0][0]))
                        date_str = date_object.strftime("%Y-%m-%d")

                        if follow_up_number <= 6:
                            follow_up_number += 1
                        else:
                            follow_up_number = 7
                        cur.execute(
                            'INSERT INTO FOLLOW_UP(activity_register,date_to_be_done,next_follow_up_number_id) VALUES (?,?,?)',
                            (activity_register, date_str, follow_up_number))

                        cur.execute('SELECT points FROM LIST_OF_ACTIVITIES WHERE activity_id = 26')
                        pts = cur.fetchall()
                        cur.execute('SELECT repetition FROM ACTIVITIES_DONE WHERE activity_register = ?;',
                                    (activity_register,))
                        rep = cur.fetchall()

                        follow_up_points = int(0.5 * float(pts[0][0]) * float(rep[0][0]))

                        addFollowUpPointsForTheDay(cur, conn, user_id, date_, follow_up_points)
                        #conn.commit()
                        response_msg += (article_link + '\n')
                        index += 1
            #conn.commit()

        if(command == 'give_5_words'):
            send_to = 0
            response_type = 0

            cur.execute('''SELECT word,meaning FROM VOCABULARY WHERE activity_register
            IN(SELECT activity_register FROM ACTIVITIES_DONE WHERE
            user_id = ? AND activity_id = 27)''',(user_id,))
            words_list = cur.fetchall()
            no_of_words = min(5, len(words_list))
            rand_words = random.sample(words_list, no_of_words)

            response_msg = ''

            for index_1 in range(no_of_words):
                response_msg += (rand_words[index_1][0] + ' - ' + rand_words[index_1][1] + '\n')

            if(len(words_list)==0):
                response_msg = 'You have not learnt any word with our app'

        if(command == 'wake'):
            now = datetime.now()
            time_ = now.strftime("%H:%M")
            try:
                w_time = time_
                arr = w_time.split(':')
                hour = int(arr[0])
                mini = int(arr[1])
                if 0 <= hour < 24 and 0 <= mini < 60:
                    now = datetime.now()
                    date_ = now.strftime("%Y-%m-%d")
                    if hour < 4:
                        pts = 250
                    elif hour < 8:
                        offset = ((hour - 4) * 60 + mini)
                        offset = (240 - offset) / 10
                        pts = int(3.14477880 * (1.2 ** offset))
                    elif hour < 12:
                        offset = ((hour - 8) * 60 + mini)
                        offset = offset / 10
                        pts = int(-3.14477880 * (1.2 ** offset))
                    else:
                        pts = -250
                    f_time = ''
                    if hour < 10:
                        f_time = '0'
                    f_time = f_time + str(hour) + ":"
                    if mini < 10:
                        f_time = f_time + '0'
                    f_time = f_time + str(mini)

                    cur.execute("SELECT wake_up_time FROM wake_up_time where user_id = ? and date_ = ?;",
                                (user_id, date_))
                    result = cur.fetchall()
                    if not result:
                        cur.execute(
                            'INSERT INTO wake_up_time(user_id,date_,wake_up_time,pts_fetched) VALUES (?,?,?,?);',
                            (user_id, date_, f_time, pts))
                        addActivityPointsForTheDay(cur, conn, user_id, date_, pts)
                        #conn.commit()
                        response_msg = 'You got ' + str(pts) + " points tday for waking up at " + str(f_time)
                        return 0, 0, file_location, response_msg

                    else:
                         response_msg = 'You already informed us that you woke up at {}'.format(result[0][0])
                         return 0, 0, file_location, response_msg
                else:
                    send_to = 0
                    response_type = 0
                    response_msg = 'Some unexpected error occured.'
                    return send_to, response_type, file_location, response_msg

            except:
                send_to = 0
                response_type = 0
                response_msg = 'Some unexpected error occured'
                return send_to, response_type, file_location, response_msg

        if(command == 'day_wise_pts'):
            today_date = date.today()
            td = timedelta(28)

            today_date = today_date - td
            today_date = today_date.strftime("%Y-%m-%d")

            cur.execute(
                'SELECT *,sum(follow_up_points+activity_points) as total FROM points WHERE user_id=? AND date_ > ? GROUP BY user_id,date_ ORDER BY date_;',
                (user_id,today_date))
            rank_result = cur.fetchall()
            dates=[]
            points=[]

            for i in rank_result:
                dates.append(i[1])
                points.append(i[4])

            for dt in range(len(dates)):
                dates[dt] = dates[dt][8:]
            #date_objects = [datetime.strptime(date, '%Y-%m-%d').date() for date in dates]
            plt.plot(dates, points, color='blue', marker='o', markerfacecolor='blue', markersize=9)

            plt.xlabel('Date - axis')
            plt.ylabel('Points - axis')
            plt.title('Points vs Date Comparison for '+user_name)

            # save that image
            now = datetime.now()
            file_name = (now.strftime("%d_%m_%Y_%H_%M_%S")) + '.png'
            file_location = 'user_data//' + command + '//' + file_name
            plt.savefig(file_location)
            plt.clf()
            plt.cla()
            plt.close()
            return 1, 1, file_location, response_msg

        if(command == 'wake_up_graph'):
            today_date = date.today()
            td = timedelta(28)

            today_date = today_date - td
            today_date = today_date.strftime("%Y-%m-%d")

            cur.execute(
                'SELECT * FROM wake_up_time WHERE user_id=? AND date_ > ? ORDER BY date_;',
                (user_id,today_date))
            rank_result = cur.fetchall()
            dates=[]
            points=[]

            for i in rank_result:
                dates.append(i[1])
                bugresolve = i[2].split(":")
                bugresolve = bugresolve[0]+'.'+bugresolve[1]
                bugresolve = float(bugresolve)
                points.append(bugresolve)

            for dt in range(len(dates)):
                dates[dt] = dates[dt][8:]

            #date_objects = [datetime.strptime(date, '%Y-%m-%d').date() for date in dates]
            plt.plot(dates, points, color='blue', marker='o', markerfacecolor='blue', markersize=9)

            plt.xlabel('Date - axis')
            plt.ylabel('TIME - axis')
            plt.title('WAKE UP TIME vs Date Comparison for '+user_name)

            # save that image
            now = datetime.now()
            file_name = (now.strftime("%d_%m_%Y_%H_%M_%S")) + '.png'
            file_location = 'user_data//' + command + '//' + file_name
            plt.savefig(file_location)
            plt.clf()
            plt.cla()
            plt.close()
            return 1, 1, file_location, response_msg

        if(command == 'weight_graph'):
            today_date = date.today()
            td = timedelta(28)

            today_date = today_date - td
            today_date = today_date.strftime("%Y-%m-%d")

            cur.execute(
                'SELECT * FROM WEIGHT WHERE user_id=? AND date_entered > ? ORDER BY date_entered;',
                (user_id,today_date))
            rank_result = cur.fetchall()
            dates=[]
            points=[]

            for i in rank_result:
                dates.append(i[0])
                points.append(float(i[2]))

            for dt in range(len(dates)):
                dates[dt] = dates[dt][8:]

            #date_objects = [datetime.strptime(date, '%Y-%m-%d').date() for date in dates]
            plt.plot(dates, points, color='blue', marker='o', markerfacecolor='blue', markersize=9)

            plt.xlabel('Date - axis')
            plt.ylabel('TIME - axis')
            plt.title('WEIGHT vs Date Comparison for '+user_name)

            # save that image
            now = datetime.now()
            file_name = (now.strftime("%d_%m_%Y_%H_%M_%S")) + '.png'
            file_location = 'user_data//' + command + '//' + file_name
            plt.savefig(file_location)
            plt.clf()
            plt.cla()
            plt.close()
            return 1, 1, file_location, response_msg

    elif(wt_msg!=''):
        #conn.commit()
        send_to = 0
        response_type = 0
        wt_msg = wt_msg.strip()
        space_sep = wt_msg.split()
        if(space_sep[0].isnumeric()):
            activity_id = int(space_sep[0])
            cur.execute('SELECT points FROM LIST_OF_ACTIVITIES WHERE activity_id = ?',(activity_id,))
            pts = cur.fetchall()

            if(len(pts)==0):
                response_msg = 'No activity with that id'
                return send_to, response_type, file_location, response_msg
            else:
                pts_for_one_rep = int(pts[0][0])

                now = datetime.now()
                date_ = now.strftime("%Y-%m-%d")
                time_ = now.strftime("%H:%M:%S")
                date_time_completed = date_ + ' ' + time_

                remaining_part = ''
                for j in range(1,len(space_sep)):
                    remaining_part += (space_sep[j] + ' ')

                remaining_part = remaining_part.strip()
                cur.execute('SELECT COUNT(activity_register) FROM ACTIVITIES_DONE')
                result = cur.fetchall()
                activity_register = int(result[0][0]) + 1

                if(activity_id>27):
                    if(remaining_part!=''):
                        if(remaining_part.isnumeric()):
                            repetition = int(remaining_part)
                        else:
                            response_msg = 'Unsupported command'
                            return send_to, response_type, file_location, response_msg
                    else:
                        repetition = 1

                    activity_points = pts_for_one_rep * repetition

                    cur.execute(
                        'INSERT INTO ACTIVITIES_DONE(activity_register,user_id,activity_id,date_time_completed,repetition) VALUES (?,?,?,?,?)',
                        (activity_register, user_id, activity_id, date_time_completed, repetition))
                    addActivityPointsForTheDay(cur, conn, user_id, date_, activity_points)
                    #conn.commit()
                    response_msg = 'You got ' + str(activity_points) + ' points for '
                    cur.execute('SELECT activity_name FROM LIST_OF_ACTIVITIES WHERE activity_id = ?',(activity_id,))
                    result = cur.fetchall()
                    activity_name = result[0][0]
                    response_msg += activity_name
                    if(repetition>1):
                        response_msg += (' (' + str(repetition) + ' times)')
                    return 0, 0, file_location, response_msg

                else:
                    repetition = 1
                    if(remaining_part.strip()==''):
                        response_msg = 'Not enough data to complete request'
                        return send_to, response_type, file_location, response_msg

                    if(activity_id==27):
                        temparr = remaining_part.split('-')
                        if(len(temparr)==1):
                            response_msg = 'No meaning given'
                            return send_to, response_type, file_location, response_msg
                        word = temparr[0]
                        meaning = temparr[1]
                        if(word == '' or meaning == ''):
                            response_msg = 'Please give both word and meaning'
                            return send_to, response_type, file_location, response_msg

                    if(activity_id==25):
                        hasError, repetition = repetition_in_book(cur, conn, remaining_part)
                        if(hasError):
                            if(repetition==-1):
                                response_msg = 'No such book exists'
                                return send_to, response_type, file_location, response_msg
                            else:
                                response_msg = 'Error in page numbers specified'
                                return send_to, response_type, file_location, response_msg
                    external_link = remaining_part

                    activity_points = pts_for_one_rep * repetition

                    cur.execute(
                        'INSERT INTO ACTIVITIES_DONE(activity_register,user_id,activity_id,date_time_completed,repetition) VALUES (?,?,?,?,?)',
                        (activity_register, user_id, activity_id, date_time_completed, repetition))
                    addActivityPointsForTheDay(cur, conn, user_id, date_, activity_points)

                    if external_link != '':  # add follow upp

                        if activity_id < 25:
                            status_id = activity_id % 4
                            if status_id == 0:
                                status_id = 4

                            if activity_id < 13:
                                cur.execute(
                                    'INSERT INTO CODECHEF(activity_register,problem_tag,status_id) VALUES (?,?,?)',
                                    (activity_register, external_link, status_id))
                                #conn.commit()
                                if(status_id == 1):
                                    response_msg = user_name + ' got ac in codechef problem tag - ' + external_link
                                    return 1, response_type, file_location, response_msg
                                else:
                                    response_msg = user_name + ' is trying codechef problem tag - ' + external_link
                                    return 1, response_type, file_location, response_msg
                            else:
                                cur.execute(
                                    'INSERT INTO CP_WEBSITES(activity_register,problem_link,status_id) VALUES (?,?,?)',
                                    (activity_register, external_link, status_id))
                                #conn.commit()
                                if(status_id == 1):
                                    response_msg = user_name + ' got ac in - ' + external_link
                                    return 1, response_type, file_location, response_msg
                                else:
                                    response_msg = user_name + ' is trying  - ' + external_link
                                    return 1, response_type, file_location, response_msg

                        if activity_id == 25:
                            # 12|1-2,3,4,7-8
                            hasError = False
                            temparr = external_link.split('|')
                            book_id = int(temparr[0])
                            arr = temparr[1].split(",")
                            cur.execute('SELECT book_id FROM BOOK WHERE book_id = ?', (book_id,))
                            result = cur.fetchall()
                            if len(result) == 0:
                                hasError = True

                            cur.execute('SELECT book_name FROM BOOK WHERE book_id = ?',(book_id,))
                            result_te = cur.fetchall()
                            book_name = result_te[0][0]
                            response_msg = user_name + ' is reading ' + book_name + ' pages:'

                            list = []
                            for i in range(len(arr)):
                                arr2 = arr[i].split("-")
                                list.append(arr2)
                                # [ [1,10], [13,15], [18] ]
                            for i in range(len(list)):
                                if len(list[i]) == 1:
                                    try:
                                        pg = int(list[i][0])
                                        if not hasError:
                                            cur.execute(
                                                'INSERT INTO BOOK_READ_REGISTER(activity_register,book_id,page_no) VALUES (?,?,?)',
                                                (activity_register, book_id, pg))
                                            response_msg += (' '+str(pg)+',')
                                    except:
                                        hasError = True

                                elif len(list[i]) == 2:
                                    try:
                                        pgstart = int(list[i][0])
                                        pgend = int(list[i][1])
                                        if pgstart <= pgend:
                                            for j in range(pgstart, pgend + 1):
                                                if not hasError:
                                                    cur.execute(
                                                        'INSERT INTO BOOK_READ_REGISTER(activity_register,book_id,page_no) VALUES (?,?,?)',
                                                        (activity_register, book_id, j))
                                                    response_msg += (''+str(j)+',')
                                    except:
                                        hasError = True
                                else:
                                    hasError = True

                            if not hasError:
                                date_str = date_
                                date_object = datetime.strptime(date_str, '%Y-%m-%d').date()
                                date_object = date_object + timedelta(days=1)
                                date_str = date_object.strftime("%Y-%m-%d")
                                cur.execute(
                                    'INSERT INTO FOLLOW_UP(activity_register,date_to_be_done,next_follow_up_number_id) VALUES (?,?,?)',
                                    (activity_register, date_str, 2))
                            response_msg = response_msg[:len(response_msg)-1]
                            #conn.commit()

                            return 1, response_type, file_location, response_msg

                        if activity_id == 26:
                            cur.execute('INSERT INTO ARTICLES(activity_register,article_link) VALUES (?,?)',
                                        (activity_register, external_link))
                            date_str = date_
                            date_object = datetime.strptime(date_str, '%Y-%m-%d').date()
                            date_object = date_object + timedelta(days=1)
                            date_str = date_object.strftime("%Y-%m-%d")
                            cur.execute(
                                'INSERT INTO FOLLOW_UP(activity_register,date_to_be_done,next_follow_up_number_id) VALUES (?,?,?)',
                                (activity_register, date_str, 2))
                            response_msg = user_name + ' read ' + external_link
                            #conn.commit()

                            return 1, response_type, file_location, response_msg

                        if activity_id == 27:
                            temparr = external_link.split('-')
                            word = temparr[0]
                            meaning = temparr[1]
                            cur.execute(
                                'INSERT INTO VOCABULARY(activity_register,word,meaning) VALUES (?,?,?)',
                                (activity_register, word, meaning))
                            date_str = date_
                            date_object = datetime.strptime(date_str, '%Y-%m-%d').date()
                            date_object = date_object + timedelta(days=1)
                            date_str = date_object.strftime("%Y-%m-%d")
                            cur.execute(
                                'INSERT INTO FOLLOW_UP(activity_register,date_to_be_done,next_follow_up_number_id) VALUES (?,?,?)',
                                (activity_register, date_str, 2))
                            response_msg = 'Congratulations on learning a new word'
                            #conn.commit()

                            return 0, response_type, file_location, response_msg
                #conn.commit()


        elif(space_sep[0].lower()=='give'):
            if(len(space_sep)!=3):
                response_msg = 'Unsupported operation'
                return 0, 0, file_location, response_msg
            if(not(space_sep[1].isnumeric())):
                response_msg = 'Please provide a number'
                return 0, 0, file_location, response_msg
            if(space_sep[2].lower()=='words' or space_sep[2].lower()=='word'):
                send_to = 0
                response_type = 0

                cur.execute('''SELECT word,meaning FROM VOCABULARY WHERE activity_register
                IN(SELECT activity_register FROM ACTIVITIES_DONE WHERE
                user_id = ? AND activity_id = 27)''',(user_id,))
                words_list = cur.fetchall()
                no_of_words = min(int(space_sep[1]), len(words_list))
                rand_words = random.sample(words_list, no_of_words)

                response_msg = ''

                for index_1 in range(no_of_words):
                    response_msg += (rand_words[index_1][0] + ' - ' + rand_words[index_1][1] + '\n')

                if(len(words_list)==0):
                    response_msg = 'You have not learnt any word with our app'

            elif(space_sep[2].lower()=='articles' or space_sep[2].lower()=='article'):
                send_to = 0
                response_type = 0

                cur.execute('''SELECT article_link FROM ARTICLES WHERE activity_register
                IN(SELECT activity_register FROM ACTIVITIES_DONE WHERE
                user_id = ? AND activity_id = 26)''',(user_id,))
                article_list = cur.fetchall()
                no_of_articles = min(int(space_sep[1]), len(article_list))
                rand_art = random.sample(article_list, no_of_articles)

                response_msg = ''

                for index_1 in range(no_of_articles):
                    response_msg += (rand_art[index_1][0]+'\n')

                if(len(article_list)==0):
                    response_msg = 'You have not read any article with our app'

        elif(space_sep[0].lower()=='hour'):
            if(len(space_sep)==1):
                now = datetime.now()
                date_ = now.strftime("%Y-%m-%d")
            elif(len(space_sep)==2):
                try:
                    temp_date = datetime.strptime(space_sep[1], '%Y-%m-%d')
                    date_ = temp_date.strftime("%Y-%m-%d")
                except ValueError:
                    send_to = 0
                    response_type = 0
                    response_msg = 'Please provide date in YYYY-MM-DD format'
                    return send_to, response_type, file_location, response_msg
            else:
                send_to = 0
                response_type = 0
                response_msg = 'Unsupported Operation'
                return send_to, response_type, file_location, response_msg

            total_pts = 0
            points_list = []
            hour_list = []

            send_to = 0
            response_type = 1

            for start_hr in range(0, 24):
                end_hr = start_hr + 1
                start_time = str(date_) + ' ' + str(start_hr) + ':00:00'
                end_time = str(date_) + ' ' + str(end_hr) + ':00:00'
                if start_hr < 10:
                    start_time = str(date_) + ' 0' + str(start_hr) + ':00:00'
                if end_hr < 10:
                    end_time = str(date_) + ' 0' + str(end_hr) + ':00:00'
                cur.execute(
                    'SELECT a.date_time_completed,l.activity_name,l.points,a.repetition FROM ACTIVITIES_DONE a, '
                    'LIST_OF_ACTIVITIES l WHERE a.date_time_completed>= ? AND a.date_time_completed< ? AND '
                    'a.activity_id = l.activity_id AND a.user_id= ? ORDER BY a.date_time_completed',
                    (start_time, end_time, user_id))
                sub_total = 0
                result1 = cur.fetchall()
                flag = 0

                for j in result1:
                    temp = int(j[2]) * int(j[3])
                    sub_total += temp
                    total_pts += temp

                points_list.append(sub_total)
                hour_list.append(start_hr + 0.5)

            cur.execute('SELECT follow_up_points, activity_points FROM POINTS WHERE user_id = ? AND date_ = ?',(user_id,date_))
            result = cur.fetchall()
            if(len(result)==0):
                act_pt = 0
                fol_pt = 0
            else:
                act_pt = int(result[0][1])
                fol_pt = int(result[0][0])

            cur.execute('SELECT pts_fetched FROM wake_up_time WHERE user_id = ? AND date_ = ?',(user_id,date_))
            result = cur.fetchall()
            if(len(result)==0):
                wake_pt = 0
            else:
                wake_pt = int(result[0][0])

            total_pt = act_pt + fol_pt
            act_pt -= wake_pt

            act = 'ACTIV_PTS-'+str(act_pt)
            fol = 'FOLUP_PTS-'+str(fol_pt)
            wak = 'WAKE_PTS-'+str(wake_pt)

            plt.plot(hour_list, points_list, color='blue', marker='o', markerfacecolor='blue', markersize=9)
            plt.xlabel('Hour - axis')
            plt.ylabel('Points - axis')
            total_pts_str = 'Total Points on [' + date_ + '] - ' + str(total_pt) + ' points (' + user_name +')'
            #plt.figtext(.4, .9, total_pts_str)
            plt.title(total_pts_str)

            red_path = mpatches.Patch(color='red',label=act)
            green_path = mpatches.Patch(color='green',label=fol)
            blue_path = mpatches.Patch(color='blue',label=wak)
            plt.legend(handles=[red_path,green_path,blue_path])
            # save that image
            now = datetime.now()
            file_name = (now.strftime("%d_%m_%Y_%H_%M_%S")) + '.png'
            file_location = 'user_data//hourly_report//' + file_name
            plt.savefig(file_location)
            plt.clf()
            plt.cla()
            plt.close()
            return 1, 1, file_location, response_msg

        elif(space_sep[0].lower()=='weight'):
            if(len(space_sep)!=2):
                send_to = 0
                response_type = 0
                response_msg = 'Please provide data in the specified format'
                return send_to, response_type, file_location, response_msg
            try:
                weight = float(space_sep[1])
                now = datetime.now()
                date_ = now.strftime("%Y-%m-%d")
                cur.execute('SELECT weight FROM WEIGHT WHERE date_entered = ? AND user_id = ?',(date_,user_id))
                result_4 = cur.fetchall()
                if(len(result_4)==0):
                    cur.execute('INSERT INTO WEIGHT VALUES (?,?,?)', (date_, user_id,weight))
                    #conn.commit()
                    send_to = 0
                    response_type = 0
                    response_msg = 'Your weight today - ' + str(weight)
                    return send_to, response_type, file_location, response_msg
                else:
                    old_weight = float(result_4[0][0])
                    cur.execute('UPDATE WEIGHT SET weight = ? WHERE date_entered = ? AND user_id = ?', (weight, date_, user_id))
                    #conn.commit()
                    send_to = 0
                    response_type = 0
                    response_msg = 'Your weight today updated from ' + str(old_weight) + ' to ' + str(weight)
                    return send_to, response_type, file_location, response_msg
            except:
                send_to = 0
                response_type = 0
                response_msg = 'Please provide valid weight'
                return send_to, response_type, file_location, response_msg

        elif(space_sep[0].lower()=='woke' or space_sep[0].lower()=='wake'):
            if(len(space_sep)==1):
                now = datetime.now()
                time_ = now.strftime("%H:%M")
            elif(len(space_sep)==2):
                try:
                    temp_time = datetime.strptime(space_sep[1], '%H:%M')
                    time_ = temp_time.strftime("%H:%M")
                except ValueError:
                    send_to = 0
                    response_type = 0
                    response_msg = 'Please provide date in HH:MM format'
                    return send_to, response_type, file_location, response_msg
            else:
                send_to = 0
                response_type = 0
                response_msg = 'Unsupported Operation'
                return send_to, response_type, file_location, response_msg
            try:
                w_time = time_
                arr = w_time.split(':')
                hour = int(arr[0])
                mini = int(arr[1])
                if 0 <= hour < 24 and 0 <= mini < 60:
                    now = datetime.now()
                    date_ = now.strftime("%Y-%m-%d")
                    if hour < 4:
                        pts = 250
                    elif hour < 8:
                        offset = ((hour - 4) * 60 + mini)
                        offset = (240 - offset) / 10
                        pts = int(3.14477880 * (1.2 ** offset))
                    elif hour < 12:
                        offset = ((hour - 8) * 60 + mini)
                        offset = offset / 10
                        pts = int(-3.14477880 * (1.2 ** offset))
                    else:
                        pts = -250
                    f_time = ''
                    if hour < 10:
                        f_time = '0'
                    f_time = f_time + str(hour) + ":"
                    if mini < 10:
                        f_time = f_time + '0'
                    f_time = f_time + str(mini)

                    cur.execute("SELECT wake_up_time FROM wake_up_time where user_id = ? and date_ = ?;",
                                (user_id, date_))
                    result = cur.fetchall()
                    if not result:
                        cur.execute(
                            'INSERT INTO wake_up_time(user_id,date_,wake_up_time,pts_fetched) VALUES (?,?,?,?);',
                            (user_id, date_, f_time, pts))
                        addActivityPointsForTheDay(cur, conn, user_id, date_, pts)
                        #conn.commit()
                        response_msg = 'You got ' + str(pts) + " points tday for waking up at " + str(f_time)
                        return 0, 0, file_location, response_msg

                    else:
                         response_msg = 'You already informed us that you woke up at {}'.format(result[0][0])
                         return 0, 0, file_location, response_msg
                else:
                    send_to = 0
                    response_type = 0
                    response_msg = 'Some unexpected error occured.'
                    return send_to, response_type, file_location, response_msg

            except:
                send_to = 0
                response_type = 0
                response_msg = 'Some unexpected error occured'
                return send_to, response_type, file_location, response_msg

        elif(space_sep[0].lower()=='add'):
            if(len(space_sep)<=2):
                response_msg = 'Unsupported operation'
                return 0, 0, file_location, response_msg
            if(space_sep[1].lower()=='book' or space_sep[1].lower()=='activity'):
                pass
            else:
                response_msg = 'Unsupported operation'
                return 0, 0, file_location, response_msg
            if(space_sep[1].lower()=='book'):
                book_name = ''
                for bk in range(2,len(space_sep)):
                    book_name += str(space_sep[bk])
                cur.execute('SELECT book_id FROM BOOK WHERE book_name = ?',(book_name,))
                result = cur.fetchall()
                if(len(result)!=0):
                    book_id = result[0][0]
                    response_msg = 'Book already there in our database with book ID - ' + str(book_id)
                    return 0, 0, file_location, response_msg
                else:
                    cur.execute('SELECT count(book_id) FROM BOOK')
                    result = cur.fetchall()

                    book_id = int(result[0][0]) + 1
                    book_id = str(book_id)

                    cur.execute('INSERT INTO BOOK VALUES (?,?)',(book_id, book_name))
                    #conn.commit()

                    response_msg = 'Use Book ID - ' + book_id
                    return 0, 0, file_location, response_msg

            if(space_sep[1].lower()=='activity'):
                if(len(space_sep)<5):
                    response_msg = 'Unsupported operation'
                    return 0, 0, file_location, response_msg
                try:
                    category_id = space_sep[2]
                    if(category_id not in ['1','2','3','4']):
                        response_msg = 'Provide a valid Category ID'
                        return 0, 0, file_location, response_msg
                    points = int(space_sep[-1])
                    activity_name = ''
                    for inde in range(3,(len(space_sep)-1)):
                        activity_name += (space_sep[inde] + ' ')

                    cur.execute('SELECT activity_id FROM LIST_OF_ACTIVITIES WHERE activity_name = ?',(activity_name,))
                    result = cur.fetchall()
                    if(len(result)!=0):
                        response_msg = 'That activity is already available with Activity ID ' + str(result[0][0])
                        return 0, 0, file_location, response_msg

                    cur.execute('SELECT count(activity_id) FROM LIST_OF_ACTIVITIES')
                    result = cur.fetchall()
                    activity_id = int(result[0][0]) + 1

                    cur.execute('INSERT INTO LIST_OF_ACTIVITIES VALUES (?,?,?,?)',(activity_id,category_id,activity_name,points))
                    #conn.commit()

                    response_msg = user_name + ' inserted an activity "' + activity_name
                    response_msg += '" under category ' + str(category_id) + ' with ' + str(points) + ' points for one repetition. '
                    response_msg += 'Feel free to use it with Activity ID ' + str(activity_id)
                    return 1, 0, file_location, response_msg
                except:
                    response_msg = 'Please use the specified format'
                    return 0, 0, file_location, response_msg

            response_msg = 'Please use the specified format'
            return 0, 0, file_location, response_msg

        elif(space_sep[0].lower()=='books'):
            cur.execute('SELECT * FROM BOOK')
            book_list = cur.fetchall()

            response_msg = ''
            for inde in range(len(book_list)):
                response_msg += (str(book_list[inde][0]) + '. ' + str(book_list[inde][1]) + '\n')

            return 0, 0, file_location, response_msg

        elif(space_sep[0].lower()=='activities'):
            cur.execute('SELECT * FROM LIST_OF_ACTIVITIES')
            act_list = cur.fetchall()

            response_msg = ''
            for inde in range(len(act_list)):
                response_msg += (str(act_list[inde][0]) + '. ' + str(act_list[inde][2]) + ' - ' + str(act_list[inde][3]) + ' pts\n')

            return 0, 0, file_location, response_msg

        elif(space_sep[0].lower()=='word'):
            if(len(space_sep)!=3):
                response_msg = 'Please provide word word_start_no word_end_no'
                return 0, 0, file_location, response_msg
            try:
                cur.execute('''SELECT word,meaning FROM VOCABULARY WHERE activity_register
                IN(SELECT activity_register FROM ACTIVITIES_DONE WHERE
                user_id = ? AND activity_id = 27)''',(user_id,))
                words_list = cur.fetchall()

                response_msg = 'You have read a total of ' + str(len(words_list)) + ' words so far.\n'
                start = int(space_sep[1])
                end = int(space_sep[2])
                if(start>len(words_list)):
                    response_msg += 'Please ask for words in that range'
                    return 0, 0, file_location, response_msg
                if(start>end):
                    response_msg += 'Start must be less than end.'
                    return 0, 0, file_location, response_msg
                if(len(words_list)<end):
                    end = len(words_list)
                for inde in range(start-1,end):
                    response_msg += (str(inde+1) + '. ' + words_list[inde][0] + ' - ' + words_list[inde][1] + '\n')
                return 0, 0, file_location, response_msg
            except:
                response_msg = 'Please provide word word_start_no word_end_no'
                return 0, 0, file_location, response_msg

        else:
            response_msg = 'Unsupported operation'
            return 0, 0, file_location, response_msg
    return send_to, response_type, file_location, response_msg

#conn = sqlite3.connect('productivity.sqlite')
#cur = conn.cursor()

#process_response(cur, conn, user_name, user_id, wt_msg, command)
#print(process_response(cur,conn,'nandykishfast',1,'','day_wise_pts'))
#print(repetition_in_book('1|1,2,3,5-7,9-10'))
