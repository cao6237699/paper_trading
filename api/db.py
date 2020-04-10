
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

from paper_trading.utility.model import DBData


class MongoDBService():
    """MONGODB数据库服务类"""

    def __init__(self, host, port):
        """构造函数"""
        self.db_client = None  # 数据库对象
        self.connected = False  # 数据库连接状态
        self.host = host
        self.port = port

    def connect_db(self):
        """连接数据库"""
        try:
            if not self.db_client:
                # 读取MongoDB的设置
                # 设置MongoDB操作的超时时间为0.5秒
                self.db_client = MongoClient(
                    self.host,
                    self.port,
                    connectTimeoutMS=500)

                # 调用server_info查询服务器状态，防止服务器异常并未连接成功
                self.db_client.server_info()
                self.connected = True

            return True
        except:
            raise ConnectionFailure("MongoDB数据库连接失败")

    def on_query_one(self, pt_db: DBData):
        """数据库查询操作"""
        try:
            db = self.db_client[pt_db.db_name]
            cl = db[pt_db.db_cl]
            flt = pt_db.raw_data['flt']
            result = cl.find_one(flt)

            return result
        except:
            raise OperationFailure("MongoDB数据库查询数据失败")

    def on_select(self, pt_db: DBData):
        """数据库查询操作"""
        try:
            db = self.db_client[pt_db.db_name]
            cl = db[pt_db.db_cl]
            flt = pt_db.raw_data['flt']
            result = cl.find(flt)

            return result
        except:
            raise OperationFailure("MongoDB数据库查询数据失败")

    def on_insert(self, pt_db: DBData):
        """数据库插入数据操作"""
        try:
            db = self.db_client[pt_db.db_name]
            cl = db[pt_db.db_cl]
            data = pt_db.raw_data['data']
            row = data.__dict__
            cl.insert_one(row)
            return True
        except:
            raise OperationFailure("MongoDB数据库插入数据失败")

    def on_insert_many(self, pt_db: DBData):
        """数据库插入数据操作"""
        try:
            db = self.db_client[pt_db.db_name]
            cl = db[pt_db.db_cl]
            row = pt_db.raw_data['data']
            cl.insert_many(row)
            return True
        except:
            raise OperationFailure("MongoDB数据库插入数据失败")

    def on_replace_one(self, pt_db: DBData):
        """数据库插入数据操作"""
        try:
            db = self.db_client[pt_db.db_name]
            cl = db[pt_db.db_cl]
            flt = pt_db.raw_data['flt']
            data = pt_db.raw_data['data']
            row = data.__dict__
            cl.replace_one(flt, row, True)
            return True
        except:
            raise OperationFailure("MongoDB数据库replace数据失败")

    def on_update(self, pt_db: DBData):
        """数据库更新操作"""
        try:
            db = self.db_client[pt_db.db_name]
            cl = db[pt_db.db_cl]
            flt = pt_db.raw_data['flt']
            set_ = pt_db.raw_data['set']
            cl.update_one(flt, set_)
            return True
        except:
            raise OperationFailure("MongoDB数据库更新数据失败")

    def on_delete(self, pt_db: DBData):
        """数据库删除操作"""
        try:
            db = self.db_client[pt_db.db_name]
            cl = db[pt_db.db_cl]
            flt = pt_db.raw_data['flt']

            return cl.delete_many(flt)

        except:
            raise OperationFailure("MongoDB数据库删除数据失败")

    def on_group(self, pt_db: DBData):
        """分组查询"""
        try:
            db = self.db_client[pt_db.db_name]
            cl = db[pt_db.db_cl]
            flt = pt_db.raw_data['flt']
            group = pt_db.raw_data['group']
            result = cl.aggregate([flt, group])

            return result
        except:
            raise OperationFailure("MongoDB数据库分组查询数据失败")

    def on_collections_query(self, pt_db: DBData):
        """获取集合列表"""
        try:
            db = self.db_client[pt_db.db_name]
            cl_names = list(db.list_collection_names())

            return cl_names
        except:
            raise OperationFailure("MongoDB数据库查询所有集合名称失败")

    def on_collection_delete(self, pt_db: DBData):
        """数据库集合删除"""
        try:
            db = self.db_client[pt_db.db_name]
            cl = db[pt_db.db_cl]
            cl.drop()
            return True
        except:
            raise OperationFailure("MongoDB数据库集合删除失败")

    def close(self):
        """数据服务关闭"""
        self.connected = False

        if self.db_client:
            self.db_client.close()
        self.db_client = None
