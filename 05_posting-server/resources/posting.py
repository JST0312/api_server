from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from mysql.connector import Error

from flask_jwt_extended import get_jwt_identity
from config import Config

from mysql_connection import get_connection

from datetime import datetime

import boto3


class PostingListResource(Resource) :
    
    @jwt_required()
    def post(self) :

        # 1. 클라이언트가 보낸 데이터를 받는다.
        if 'photo' not in request.files :
            return {'error' : '파일을 업로드 하세요'}, 400

        if 'content' not in request.form :
            return {'error' : '내용은 필수입니다.'}, 400

        file = request.files['photo']
        content = request.form['content']

        user_id = get_jwt_identity()


        # 2. 사진을 먼저 S3에 저장
        ### 2-1. aws 콘솔로 가서 IAM 유저 만든다.(없으면 만든다)
        ### 2-2. s3 로 가서 이 프로젝트의 버킷을 만든다.
        ### 2-3. config.py 에 적어준다.

        ### 2-4. 파일명을 유니크하게 만든다.
        current_time = datetime.now()
        new_file_name = str(user_id) + current_time.isoformat().replace(':','_')+'.jpg'

        file.filename = new_file_name
        
        ### 2-5. S3에 파일 업로드 한다.
        ###      파일 업로드하는 코드는! boto3라이브러리를
        ###      이용해서 업로드한다.
        ###      라이브러리가 설치안되어있으면, pip install boto3 로 설치한다.
        client = boto3.client('s3', 
                    aws_access_key_id = Config.ACCESS_KEY,
                    aws_secret_access_key = Config.SECRET_ACCESS)
        try :
            client.upload_fileobj(file,
                                    Config.S3_BUCKET,
                                    new_file_name,
                                    ExtraArgs = {'ACL':'public-read', 'ContentType' : file.content_type } )
        
        except Exception as e:
            return {'error' : str(e)}, 500


        # 3. S3에 저장된 사진을 Object Detectin 한다
        #    (AWS Rekognition 이용)
        #    Labels 안에 있는 Name 만 가져온다.
        client = boto3.client('rekognition',
                    'ap-northeast-2',
                    aws_access_key_id=Config.ACCESS_KEY,
                    aws_secret_access_key = Config.SECRET_ACCESS)

        response = client.detect_labels(Image={'S3Object':{'Bucket':Config.S3_BUCKET, 'Name':new_file_name}} ,
                            MaxLabels = 5 )

        print(response)

        name_list = []
        for row in response['Labels'] :
            name_list.append(row['Name'])        

        # 4. 위에서 나온 결과인, imgURL 과
        #    태그로 저장할 Labels 이름을 가지고
        #    DB에 저장한다.
        imgUrl = Config.S3_LOCATION + new_file_name
        try : 
            connection = get_connection()
            # 4-1. imgUrl과 content를 posting 테이블에 인서트!
            query = '''insert into posting
                    (userId, imgUrl, content)
                    values
                    (%s, %s, %s);'''
            record = (user_id, imgUrl, content )
            cursor = connection.cursor()
            cursor.execute(query, record)
            posting_id = cursor.lastrowid
            print(posting_id)

            # 4-2. tag_name 과 tag 테이블에 인서트 해준다.
            # 4-2-1. name_list 에 있는 문자열이,
            #        tag_name 테이블에 들어있는지 확인해서
            #        있으면, 그 tag_name 의 아이디를 가져오고,
            #        없으면, tag_name 에 넣어준다.
            for name in name_list :
                query = '''select *
                        from tag_name
                        where name = %s;'''
                record = (name , )
                cursor = connection.cursor(dictionary=True)
                cursor.execute(query, record)
                result_list = cursor.fetchall()
                if len(result_list) == 0 :
                    query = '''insert into tag_name
                            (name)
                            values
                            (%s);'''
                    record = (name, )
                    cursor.execute(query, record)
                    tag_id = cursor.lastrowid
                else :
                    tag_id = result_list[0]['id']


                # tag 테이블에, posting_id와 tag_id 를 
                # 저장한다.
                query = '''insert into tag
                        (postingId, tagId)
                        values
                        ( %s, %s);'''
                record = (posting_id , tag_id)
                cursor.execute(query, record)


            connection.commit()
            cursor.close()
            connection.close()        
        except Error as e:
            print(e)
            cursor.close()
            connection.close()        
            return {'error' : str(e)} , 500

        # 5. 결과를 클라이언트에 보내준다

        return {'result' : 'success'}






