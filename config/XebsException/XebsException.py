# class XebsException(BaseException):
# #     def ceph_status_err(self):
# #         print('ceph状态不正常')
# #     def badio(self):
# #         print('出现badio')
# #     def data_consistent(self):
# #         print('出现数据不一致')


class CustomError(Exception):
    def __init__(self,ErrorInfo):
        super().__init__(self) #初始化父类
        self.errorinfo=ErrorInfo
    def __str__(self):
        return self.errorinfo

class ceph_status_err(Exception):
    def __init__(self,ErrorInfo):
        super().__init__(self)
        self.errorinfo=ErrorInfo
    def __str__(self):
        return self.errorinfo
if __name__ == '__main__':
    try:
        raise ceph_status_err('CEPH集群状态异常')
    except ceph_status_err as e:
        print(e)