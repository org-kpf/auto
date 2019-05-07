#在不改变源码的情况下，修改已经存在的函数(例子中的func)，比如增加一句调试声明，以查看传入的参数
#本例中，document_it()定义了一个装饰器，会实现如下功能：1.打印输出函数的名字和参数的值，2.执行含有参数的函数,3.打印输出结果，4.返回修改后的函数
def document_it(func):
    def new_function(*args,**kwargs):
        print('Running function:',func.__name__)
        print('Positional arguments:',args)
        print('Keyword arguments:',kwargs)
        for i in kwargs:
            if i != '':
                #print ('--'+i+'=%s' %kwargs.get(i))
                print('kwargs的键是',kwargs.keys())
                print(kwargs.get(i))
        result = func(*args,**kwargs)
        print('Result:',result)
        return result
    return new_function
def add_ints(a,b):
    return a + b
cooler_add_ints = document_it(add_ints)
cooler_add_ints(a=3,b=5)