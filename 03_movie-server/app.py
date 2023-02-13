from flask import Flask
from flask_jwt_extended import JWTManager
from flask_restful import Api
from config import Config
from resources.favorite import FavoriteListResource, FavoriteResource
from resources.movie import MovieListResource, MovieResource, MovieSearchResource
from resources.recommend import MovieRecommendRealTimeResource, MovieRecommendResource
from resources.review import MovieReivewResource, ReviewListResource
from resources.user import UserLoginResource, UserLogoutResource, UserRegisterResource
from resources.user import jwt_blacklist

app = Flask(__name__)
# 환경변수 셋팅
app.config.from_object(Config)

# JWT 매니저 초기화
jwt = JWTManager(app)

# 로그아웃된 토큰으로 요청하는 경우 처리하는 코드작성.
@jwt.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header, jwt_payload) :
    jti = jwt_payload['jti']
    return jti in jwt_blacklist

api = Api(app)

# 경로와 리소스(API코드)를 연결한다.
api.add_resource(UserRegisterResource, '/user/register')
api.add_resource(UserLoginResource, '/user/login')
api.add_resource(UserLogoutResource, '/user/logout')
api.add_resource(ReviewListResource, '/review')
api.add_resource(MovieListResource, '/movie')
api.add_resource(MovieSearchResource, '/movie/search')
api.add_resource(MovieRecommendRealTimeResource, '/movie/recommend')
api.add_resource(FavoriteResource, '/favorite/<int:movie_id>')
api.add_resource(FavoriteListResource, '/favorite')
api.add_resource(MovieResource, '/movie/<int:movie_id>')
api.add_resource(MovieReivewResource, '/movie/<int:movie_id>/review')

if __name__ == '__main__' :
    app.run()
