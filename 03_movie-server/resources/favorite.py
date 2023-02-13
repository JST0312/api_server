from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from mysql.connector import Error

from flask_jwt_extended import get_jwt_identity

from mysql_connection import get_connection

class FavoriteResource(Resource) :

    @jwt_required()
    def post(self, movie_id) :

        user_id = get_jwt_identity()

        try : 
            connection = get_connection()
            query = '''insert into favorite
                    (user_id, movie_id)
                    values
                    (%s, %s);'''
            record = (user_id, movie_id)
            cursor = connection.cursor()
            cursor.execute(query, record)
            connection.commit()
            cursor.close()
            connection.close()
        except Error as e:
            print(e)
            cursor.close()
            connection.close()
            return {'error' : str(e)}, 500
        
        return {'result' : 'success'}

    @jwt_required()
    def delete(self, movie_id) :
        user_id = get_jwt_identity()

        try : 
            connection = get_connection()
            query = '''delete from favorite
                    where user_id = %s and movie_id = %s;'''
            record = (user_id, movie_id)
            cursor = connection.cursor()
            cursor.execute(query, record)
            connection.commit()
            cursor.close()
            connection.close()
        except Error as e:
            print(e)
            cursor.close()
            connection.close()
            return {'error' : str(e)}, 500
        
        return {'result' : 'success'}


class FavoriteListResource(Resource) :
    @jwt_required()
    def get(self) :

        user_id = get_jwt_identity()
        offset = request.args.get('offset')
        limit = request.args.get('limit')

        try :
            connection = get_connection()
            query = '''select f.id, f.movie_id, m.title, m.genre,
                    ifnull( count(r.movie_id) , 0) as cnt , 
                    ifnull( avg( r.rating ) , 0 )  as avg
                    from favorite f
                    join movie m
                    on f.movie_id = m.id
                    left join rating r 
                    on r.movie_id = m.id
                    where f.user_id = %s
                    group by f.movie_id
                    limit '''+offset+''', '''+limit+''';'''
            
            record = (user_id, )
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, record)
            result_list = cursor.fetchall()

            i = 0
            for row in result_list :
                result_list[i]['avg'] = float( row['avg'] )
                i = i + 1

            cursor.close()
            connection.close()
        except Error as e :
            print(e)
            cursor.close()
            connection.close()
            return {'error' : str(e)}, 500

        
        return {'result' :'success', 
                'items' : result_list, 
                'count' : len(result_list)}



