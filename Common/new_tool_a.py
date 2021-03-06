import json, re
from Common import Log
from Common import operate_json
from Conf import Config
from Common import operate_sql_al
from Common import ExcelHandler
from Common import req_reload
from Common import Assert
from Common import Consts

class New_Tool_A(object):

    def __init__(self):
        self.log = Log.MyLog()
        self.oper_j = operate_json.OperateJson()
        self.conf = Config.Config()
        self.excel = ExcelHandler.ExcelHandler()
        self.reqe = req_reload.ReqReload()
        self.test = Assert.Assertions()

    def choose_envir(self,envir):
        '''
        运行环境判断
        :param envir:
        :return: 请求url域名
        '''
        if envir =='ysy_test':
            req_url = self.conf.host_debug
        elif envir == 'yhz_test':
            req_url = self.conf.yhz_host
        elif envir =='tysy_o2o':
            req_url = self.conf.tysyo2o_host
        return req_url

    def param_get_deal(self,case):
        '''
        case参数获取并进行相关处理
        :param case:
        :return:
        '''
        envir = case['envir']
        expect = case['case_expect']
        if expect:
            expect = self.multiple_data(envir,expect)
        preset_data = case['case_preset']
        urls = case['case_url']
        global_var = case['case_global_var']
        if preset_data:
            self.multiple_data(envir, preset_data)  #返回值都写进json了
        req_url = self.choose_envir(envir)
        api_url = req_url + urls
        api_url = self.multiple_data(envir, api_url)[0]
        # api_url = self.multiple_data(envir, api_url)[0]  # 这里返回的url不该是list
        if case['case_header']:  # 判断header是否为空
            headers = json.loads(case['case_header'])
            headers = self.multiple_data(envir,headers)
        else:
            headers = None
        params = case['case_params']
        params = self.multiple_data(envir, params)  # params格式有问题
        return expect[0], api_url, headers, params, global_var          # 只验证第一个expect值即可

    def get_path(self, key, res):
        list_comma = key.split(',')
        for i in list_comma:
            list = i.split("/")
            list_last = list[-1]
            res_value = json.loads(res, encoding='utf-8')
            try:
                for i in range(len(list)):
                    if str(list[i]).isdigit():
                        res_value = res_value[int(list[i])]
                    else:
                        res_value = res_value[list[i]]
            except Exception as e:
                self.log.error('get param fail')
                raise
            self.oper_j.write_json_value(list_last, res_value)

    def response_write_to_json(self,path,response):
        '''
        写入json文件
        :param path:
        :param response:
        :return:
        '''
        self.get_path(path, response)


    def multiple_data(self,envir,data):
        '''
        对多个数据进行拆分组装，并还原;注意这里是处理了单个数据多种情况，未对多个数据多种情况进行处理---建议将三个方法拆开，合并调用
        数据如：如多个sql，或body是多个：'{"mobile":"c::","verifyCode":"j::verifyCode"}'
        :param envir:
        :param data:
        :return:list
        '''
        temp = []
        if isinstance(data,str):
            if data == '':              # 识别空param
                return data
            elif data.startswith('{'):                # dict
                result = self.brackets_data(data,envir)
                return result
            elif ';' in data:  # sql后都需要跟上";"
                split_data = data.split(';')
                for i in split_data:
                    if len(i) > 0:
                        result = self.single_sql_data_deal(envir, i)
                        if result:
                            temp.append(result)
                return temp
            else:  # 这里是实际结果，不需要任何处理的
                temp.append(self.circular_processing_data(envir, data))
                return temp
        elif isinstance(data,dict):
            result = self.brackets_dict_data(data, envir)
            return result

    # def single_sql_data_deal(self,format_data):
    #     '''
    #     首先判断'$$'，其次判断'formate',最后判断干净sql
    #     :param data:
    #     :param envir:
    #     :return:
    #     '''
    #     def inner(envir,data):
    #         oper_s = operate_sql_al.OperateSqlAl(envir)
    #         if '$$' in data and 'format' in data:
    #             # 将$$识别为即将执行sql并写入json
    #             symbol_data = data.split('$$')
    #             sql_str = format_data(envir,symbol_data[1])
    #             val = oper_s.execute_sql(sql_str)
    #             self.oper_j.write_json_value(symbol_data[0], val)
    #             return None
    #         elif "$$" in data and 'format' not in data:
    #             symbol_data = data.split('$$')
    #             sql_str = self.while_data(envir,symbol_data[1])
    #             val = oper_s.execute_sql(sql_str)
    #             self.oper_j.write_json_value(symbol_data[0], val)
    #             return None
    #         elif 'format' in data:
    #             val = format_data(envir,data)
    #             val = oper_s.execute_sql(val)
    #             return val
    #         else:
    #             val = oper_s.execute_sql(data)
    #             return val
    #     return inner

    def single_sql_data_deal(self,envir,data):
        '''
        首先判断'$$'，其次判断'formate',最后判断干净sql
        :param data:
        :param envir:
        :return:
        '''
        oper_s = operate_sql_al.OperateSqlAl(envir)
        if '$$' in data and 'format' in data:
            # 将$$识别为即将执行sql并写入json
            symbol_data = data.split('$$')
            sql_str = self.format_data(envir,symbol_data[1])
            val = oper_s.execute_sql(sql_str)
            self.oper_j.write_json_value(symbol_data[0], val)
            # return None
        elif "$$" in data and 'format' not in data:
            symbol_data = data.split('$$')
            sql_str = self.while_data(envir,symbol_data[1])
            val = oper_s.execute_sql(sql_str)
            self.oper_j.write_json_value(symbol_data[0], val)
            # return None
        elif 'format' in data:
            val = self.format_data(envir,data)
            val = oper_s.execute_sql(val)
            return val
        else:
            val = oper_s.execute_sql(data)
            return val

    def brackets_data(self,data, envir):
        '''
         处理通过“{”来输入的多个数据，比如dict， 针对dict中多个内容
        :param data:
        :param envir:
        :return:
        '''
        data = json.loads(data)  # 函数是将字符串转化为json格式字典
        for key, value in data.items():
            data[key] = self.circular_processing_data(envir, value)
        return data

    def brackets_dict_data(self,data, envir):
        '''
         处理通过dict来输入的多个数据，比如dict， 针对dict中多个内容
        :param data:
        :param envir:
        :return:
        '''
        for key, value in data.items():
            data[key] = self.circular_processing_data(envir, value)
        return data

    # @single_sql_data_deal
    def format_data(self,envir,data):
        '''
        处理数据中包含formate的待处理数据
        :param data:
        :return:
        '''
        p1 = re.compile(r"[(](.*?)[')]", re.S)  # 非贪心匹配
        split_str = data.split('format')
        var_1 = re.findall(p1, split_str[1])    # 利用正则：去掉括号
        # 这里会对list中每个值进行判断
        # var_1 = self.while_split_data(envir, var_1)  #这里怎么会传入list？
        var_1 = self.while_data(envir, var_1[0])        #这里存在format多数据暂未处理
        resutl = split_str[0].format(var_1)        # 重组sql
        return resutl

    def circular_processing_data(self,envir,data):
        '''
        循环处理数据中的变量
        :param envir:
        :param data:
        :return:
        '''
        if isinstance(data, str):
            data = self.split_data(envir,data)
        elif isinstance(data, list):
            new_data = []
            for i in data:
                i = self.split_data(envir, i)
                new_data.append(i)
            return new_data
        return  data

    def split_data(self,envir,data):
        '''
        区分str中是否带有’&‘标识：有：首先split变量,
        :param data:
        :return:
        '''
        if '&' in data:
            data = data.split("&")
            result = []
            for i in data:
                i = self.while_data(envir,i)
                result.append(i)
            temp = '&'
            data = temp.join(result)
        else:
            data = self.while_data(envir,data)
        return data


    def while_data(self,envir,data):
        '''
        持续判断data中是否包含以下几种类型变量，如果有，则对每种情况处理一次
        :param data:
        :return:
        '''
        oper_s = operate_sql_al.OperateSqlAl(envir)
        while 'j::' in data or 'c::' in data or 's::' in data:
            if 'j::' in data:
                symbol_data = data.split('j::')     # 这里有可能是body中的某个值传入，如：'j::verifyCode'
                con_data = self.oper_j.get_json_value(symbol_data[1])
                data = symbol_data[0] + con_data
                return data
            elif 'c::' in data:
                symbol_data = data.split('c::')
                con_data = self.con_var(symbol_data[1])
                data = symbol_data[0] + con_data
                return data
            elif 's::' in data:
                symbol_data = data.split('s::')
                con_data = oper_s.sql_main(symbol_data[1])     #這裡不能調用con_var方法
                data = con_data
                return data
            else:
                return data
                break
        else:
            return data

    # def split_dollar(self,envir,data):
    #     '''
    #     处理data中包含$分隔符，比如URL中包含：/api/v1/area/repair/favoriteAndTypes?userId=j::userId&biotopeId=j::biotopeId
    #     :param data:
    #     :return:
    #     '''
        # if '&' in data:
        #     data = data.split("&")
        #     result = []
        #     for i in data:
        #         i = self.while_data(envir,i)
        #         result.append(i)
        #     temp = '&'
        #     data = temp.join(result)
        #     return data
        # else:
        #     return data

    def con_var(self,var):
        if var == 'tester_debug':
            temp_con_var = self.conf.tester_debug
        elif var == 'environment_debug':
            temp_con_var = self.conf.environment_debug
        elif var == 'host_debug':
            temp_con_var = self.conf.host_debug
        elif var == 'tester_release':
            temp_con_var = self.conf.tester_release
        elif var == 'environment_release':
            temp_con_var = self.conf.environment_release
        elif var == 'host_release':
            temp_con_var = self.conf.host_release
        else:
            temp_con_var = var
        return temp_con_var

    def test_case_method(self,case,request_method):
        '''
        所有测试用例调用该方法
        :param case:
        :param request_method:
        :return:
        '''
        expect, api_url, headers, params, global_var = self.param_get_deal(case)
        response = self.reqe.req(request_method, api_url, params, headers, global_var)
        if global_var:
            self.response_write_to_json(global_var, response['text'])
        self.test.assert_common(response['code'], response['body'], expect, response['time_consuming'])
        Consts.RESULT_LIST.append('True')
        print('运行case为：{0}，验证：{1}，预期结果为：{2}'.format(case['module'], case['case_description'], expect))

if __name__ == '__main__':
    ut = New_Tool_A()
    # print(ut.while_split_data('test_debug',"s::SELECT IFNULL(dv.version,'error_version') FROM data_version dv WHERE dv.code='ios'"))
    # print(ut.split_data(''))
