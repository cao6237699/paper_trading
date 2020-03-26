## Paper trading接口文档

##### 1.创建账户

###### 简要描述：

 • 创建账户接口

###### 请求 URL：

 • /creat

###### 请求方式： 

• POST

###### 请求Headers：

content-type:form-data

###### 请求参数： 

| key  | 必需 |         value         |            备注             |
| :--: | :--: | :-------------------: | :-------------------------: |
| info |  是  | {"username":"fengbo"} | value值填写随意，返回为data |

###### 返回正确示例：

```
{

     "data": "KV3aHGalh8so7nQfHBq5",

     "status": true

}
```



###### 返回错误示例：

```
{
    "data": "请求参数错误",
    "status": false
}
```

###### 接口测试结果：

- [x] 接口使用正常		缺陷：value值填写随意，符合form-data格式返回data为token值

##### 2.查询所有账户列表

###### 简要描述：

 • 查询账户列表接口

###### 请求 URL：

 • /list

###### 请求方式： 

• GET

###### 请求Headers：

content-type:form-data

###### 请求参数： 

| key  | 必需 | value | 备注 |
| :--: | :--: | :---: | :--: |
|  无  |      |       |      |



###### 返回正确示例：

```
{
    "data": [
        "FuZ0oT8eA39AYeATid2X",
        "fdGuu6QPw6bmsSQ1g7hB",
        "bhqHtcpPxJ0kT7hpNIsZ",
        "VxGogJwrKkpTfg5OZK6H",
        "XOdgvXMZ7sXxXSKduXLc",
        "ho9iTAvm9rfiK3yXuWGk",
        "BY8b8qRWfDSlDA39PkPl",
        "XjB5LVZwsAOVsdUbuyhj",
        "3aQP3lOcj1CDaMFRUIuc",
        "H44OFKkstkGcUFXY5ua1",
        "KV3aHGalh8so7nQfHBq5"
    ],
    "status": true
}
```

###### 返回错误示例：

```

```

###### 接口测试结果：

- [x] 接口使用正常

##### 3.删除账户

###### 简要描述：

 • 删除账户接口

###### 请求 URL：

 • /delete

###### 请求方式： 

• POST

###### 请求Headers：

content-type:form-data

###### 请求参数： 

|  key  | 必需 |        value         |  说明  |
| :---: | :--: | :------------------: | :----: |
| token |  是  | 3MJSA34geOJ4VHUy88s1 | 账号id |

###### 返回正确示例：

```
{
    "data": "账户删除成功",
    "status": true
}
```

###### 返回错误示例：

```
{
    "data": "账户不存在",
    "status": false
}
```

###### 接口测试结果：

- [x] 接口使用正常

##### 4.查询账户信息

###### 简要描述：

 • 查询账户接口

###### 请求 URL：

 • /account

###### 请求方式： 

• POST

###### 请求Headers：

content-type:form-data

###### 请求参数： 

|  key  | 必需 |        value         |  说明  |
| :---: | :--: | :------------------: | :----: |
| token |  是  | nYf82sYLNoMT7T8mdvf4 | 账号id |

###### 返回正确示例：

```
{
    "data": {
        "account_id": "nYf82sYLNoMT7T8mdvf4",
        "account_info": "",
        "assets": 1000000.0,
        "available": 1000000.0,
        "captial": 1000000.0,
        "cost": 0.0003,
        "market_value": 0.0,
        "slipping": 0.01,
        "tax": 0.001
    },
    "status": true
}
```

###### 返回错误示例：

```
{
    "data": "查询账户失败",
    "status": false
}
```

###### 接口测试结果：

- [x] 接口使用正常

##### 5.查询持仓信息

###### 简要描述：

 • 查询持仓接口

###### 请求 URL：

 • /pos

###### 请求方式： 

• POST

###### 请求Headers：

content-type:form-data

###### 请求参数： 

|  key  | 必需 |        value         |  说明  |
| :---: | :--: | :------------------: | :----: |
| token |  是  | nYf82sYLNoMT7T8mdvf4 | 账号id |

###### 返回正确示例：

```
{
    "data": [
        {
            "account_id": "nYf82sYLNoMT7T8mdvf4",
            "available": 0,
            "buy_date": "20200324",
            "buy_price": 9.38,
            "code": "600520",
            "exchange": "SH",
            "now_price": 9.38,
            "profit": -105.0,
            "pt_symbol": "600520.SH",
            "volume": 37500
        }
    ],
    "status": true
}
```

###### 返回错误示例：

```
{
    "data": "请求参数错误",
    "status": false
}
```

###### 接口测试结果：

- [x] 接口使用正常

##### 6.查询所有订单

###### 简要描述：

 • 查询所有订单接口

###### 请求 URL：

 • /orders

###### 请求方式： 

• POST

###### 请求Headers：

content-type:form-data

###### 请求参数： 

|  key  | 必需 |        value         |  说明  |
| :---: | :--: | :------------------: | :----: |
| token |  是  | nYf82sYLNoMT7T8mdvf4 | 账号id |

###### 返回正确示例：

```
{
    "data": [
        {
            "account_id": "nYf82sYLNoMT7T8mdvf4",
            "code": "600050",
            "error_msg": "",
            "exchange": "SH",
            "order_date": "20200325",
            "order_id": "1585106675.2576077",
            "order_price": 5.31,
            "order_time": "11:23",
            "order_type": "buy",
            "price_type": "market",
            "product": "股票",
            "pt_symbol": "600050.SH",
            "status": "已撤销",
            "trade_price": 5.32,
            "trade_type": "t0",
            "traded": 200,
            "volume": 100
        },
        {
            "account_id": "nYf82sYLNoMT7T8mdvf4",
            "code": "600050",
            "error_msg": "",
            "exchange": "SH",
            "order_date": "20200325",
            "order_id": "1585106802.369447",
            "order_price": 5.38,
            "order_time": "11:26",
            "order_type": "buy",
            "price_type": "market",
            "product": "股票",
            "pt_symbol": "600050.SH",
            "status": "未成交",
            "trade_price": 5.38,
            "trade_type": "t0",
            "traded": 100,
            "volume": 100
        },
        {
            "account_id": "nYf82sYLNoMT7T8mdvf4",
            "code": "600520",
            "error_msg": "",
            "exchange": "SH",
            "order_date": "20200324",
            "order_id": "1585120789.3423386",
            "order_price": 12,
            "order_time": "14:46",
            "order_type": "buy",
            "price_type": "市价",
            "product": "股票",
            "pt_symbol": "600520.SH",
            "status": "全部成交",
            "trade_price": 9.38,
            "trade_type": "t1",
            "traded": 13300,
            "volume": 100
        }
    ],
    "status": true
}
```

###### 返回错误示例：

```
{
    "data": "请求参数错误",
    "status": false
}
```

###### 接口测试结果：

- [x] 接口使用正常

##### 7.查询当日订单

###### 简要描述：

 • 查询当日订单接口

###### 请求 URL：

 • /orders_today

###### 请求方式： 

• POST

###### 请求Headers：

content-type:form-data

###### 请求参数： 

|  key  | 必需 |        value         |  说明  |
| :---: | :--: | :------------------: | :----: |
| token |  是  | nYf82sYLNoMT7T8mdvf4 | 账号id |

###### 返回正确示例：

```
{
    "data": [
        {
            "account_id": "nYf82sYLNoMT7T8mdvf4",
            "code": "600050",
            "error_msg": "",
            "exchange": "SH",
            "order_date": "20200325",
            "order_id": "1585106675.2576077",
            "order_price": 5.31,
            "order_time": "11:23",
            "order_type": "buy",
            "price_type": "market",
            "product": "股票",
            "pt_symbol": "600050.SH",
            "status": "已撤销",
            "trade_price": 5.32,
            "trade_type": "t0",
            "traded": 200,
            "volume": 100
        },
        {
            "account_id": "nYf82sYLNoMT7T8mdvf4",
            "code": "600520",
            "error_msg": "",
            "exchange": "SH",
            "order_date": "20200325",
            "order_id": "1585120954.2027571",
            "order_price": 12,
            "order_time": "14:46",
            "order_type": "buy",
            "price_type": "市价",
            "product": "股票",
            "pt_symbol": "600520.SH",
            "status": "全部成交",
            "trade_price": 9.38,
            "trade_type": "t1",
            "traded": 2500,
            "volume": 100
        }
    ],
    "status": true
}
```

###### 返回错误示例：

```
{
    "data": "请求参数错误",
    "status": false
}
```

###### 接口测试结果：

- [x] 接口使用正常

##### 8.接收订单

###### 简要描述：

 • 接收订单接口

###### 请求 URL：

 • /send

###### 请求方式： 

• POST

###### 请求Headers：

content-type:form-data

###### 请求参数： 



|  key  | 必需 | value |  说明  |
| :---: | :--: | :---: | :----: |
| order |  是  |       | 账号id |

```
value值：{"code": "600520", "exchange": "SH", "account_id": "nYf82sYLNoMT7T8mdvf4", "order_id": "12", "product": "股票", "order_type": "buy", "price_type": "市价", "trade_type": "t0", "order_price":12, "trade_price": 12, "volume": 100, "traded": 100, "status": "提交中", "order_date": "20200325", "order_time": "14:46", "error_msg": ""}

```



|    参数     | 必需 | 类型  |         说明         |
| :---------: | :--: | :---: | :------------------: |
|    code     |  是  |  str  |       证券代码       |
|  exchange   |  是  |  str  |      交易所代码      |
| account_id  |  是  |  str  |     外部账户编号     |
|  order_id   |  否  |  str  |       订单编号       |
|   product   |  是  |  str  |       产品类型       |
| order_type  |  是  |  str  |       订单类型       |
| price_type  |  是  |  str  |       价格类型       |
| trade_type  |  是  |  str  | 交易类型(市价、限价) |
| order_price |  是  | float |       持仓成本       |
| trade_price |  是  | float |       成交价格       |
|   volume    |  是  | float |       交易数量       |
|   traded    |  是  | float |       成交金额       |
|   status    |  是  |  str  |       订单状态       |
| order_date  |  是  |  str  |       订单日期       |
| order_time  |  是  |  str  |       订单时长       |



###### 返回正确示例：

```
{
    "data": "1585107595.6241865",
    "status": true
}
```

###### 返回错误示例：

```
{
    "data": "请求参数错误",
    "status": false
}
```

###### 接口测试结果：

- [x] 接口使用正常

##### 9.取消订单

###### 简要描述：

 • 取消订单接口

###### 请求 URL：

 • /cancel

###### 请求方式： 

• POST

###### 请求Headers：

content-type:form-data

###### 请求参数： 



|   key    | 必需 |        value         |      说明      |
| :------: | :--: | :------------------: | :------------: |
|  token   |  是  | nYf82sYLNoMT7T8mdvf4 |     账号id     |
| order_id |      |  1585106675.2576077  | 下单时的订单号 |

###### 返回正确示例：

```
{
    "data": "撤单成功",
    "status": true
}
```

###### 返回错误示例：

```
{
    "data": "撤单失败",
    "status": false
}
```

###### 接口测试结果：

- [x] 接口使用正常

##### 10.查询订单状态

###### 简要描述：

 • 查询订单状态接口

###### 请求 URL：

 • /status

###### 请求方式： 

• POST

###### 请求Headers：

content-type:form-data

###### 请求参数： 

|   key    | 必需 |        value         |      说明      |
| :------: | :--: | :------------------: | :------------: |
|  token   |  是  | nYf82sYLNoMT7T8mdvf4 |     账号id     |
| order_id |      |  1585106675.2576077  | 下单时的订单号 |

###### 返回正确示例：

```
{
    "data": "全部成交",
    "status": true
}
```

###### 返回错误示例：

```
{
    "data": "无此订单",
    "status": false
}
```

###### 接口测试结果：

- [x] 接口使用正常

##### 11.清算

###### 简要描述：

 • 查询订单状态接口

###### 请求 URL：

 • /liquidation

###### 请求方式： 

• POST

###### 请求Headers：

content-type:form-data

###### 请求参数： 



|    key     | 必需 |        value         |  说明  |
| :--------: | :--: | :------------------: | :----: |
|   token    |  是  | nYf82sYLNoMT7T8mdvf4 | 账号id |
| check_date |  是  |       20200325       |        |
| price_dict |  是  | {"600519.0":1052.88} |        |

###### 返回正确示例：

```
{
    "data": "清算完成",
    "status": true
}
```

###### 返回错误示例：

```
{
    "data": "撤单失败",
    "status": false
}
```

###### 接口测试结果：

- [x] 接口使用正常

##### 12.获取交易报告

###### 简要描述：

 • 获取交易报告接口

###### 请求 URL：

 • /report

###### 请求方式： 

• POST

###### 请求Headers：

content-type:form-data

###### 请求参数： 



|  key  | 必需 |        value         |  说明  |
| :---: | :--: | :------------------: | :----: |
| token |  是  | nYf82sYLNoMT7T8mdvf4 | 账号id |
| start |  是  |       20200325       |        |
|  end  |  是  |       20200325       |        |

###### 返回正确示例：

```
{
    "data": {
        "annual_return": 0.0,
        "captial": 1000000.0,
        "daily_return": -2233.04,
        "end_balance": 1000000.0,
        "end_date": "20200325",
        "loss_days": 0,
        "loss_num": 2,
        "max_ddpercent": 0.0,
        "max_drawdown": 0.0,
        "profit_days": 0,
        "return_std": 2970.187892238469,
        "sharpe_ratio": -11.647110614133016,
        "start_date": "20200325",
        "total_commission": 4489.6968,
        "total_days": 1,
        "total_net_pnl": 0.0,
        "total_return": 0.0,
        "total_slippage": 0,
        "total_trade_count": 5,
        "total_turnover": 500.0,
        "win_num": 0,
        "win_rate": 0.0
    },
    "status": true
}
   
```

###### 返回错误示例：

```
{
    "data": "账户不存在",
    "status": false
}
```

###### 接口测试结果：

- [x] 接口使用正常

##### 13.获取账户记录数据

###### 简要描述：

 • 获取账户记录数据接口

###### 请求 URL：

 • /account_line

###### 请求方式： 

• POST

###### 请求Headers：

content-type:form-data

###### 请求参数： 



|  key  | 必需 |        value         |  说明  |
| :---: | :--: | :------------------: | :----: |
| token |  是  | nYf82sYLNoMT7T8mdvf4 | 账号id |
| start |  是  |       20200325       |        |
|  end  |  是  |       20200325       |        |

###### 返回正确示例：

```
{
    "data": [
        {
            "account_id": "nYf82sYLNoMT7T8mdvf4",
            "assets": 1000000.0,
            "available": 1000000.0,
            "check_date": "20200325",
            "market_value": 0
        }
    ],
    "status": true
}
```

###### 返回错误示例：

```
{
    "data": "请求参数错误",
    "status": false
}
```

###### 接口测试结果：

- [x] 接口使用正常

##### 14.获取持仓记录数据

###### 简要描述：

 • 获取持仓记录数据接口

###### 请求 URL：

 • /pos_record

###### 请求方式： 

• POST

###### 请求Headers：

content-type:form-data

###### 请求参数： 



|  key  | 必需 |        value         |  说明  |
| :---: | :--: | :------------------: | :----: |
| token |  是  | nYf82sYLNoMT7T8mdvf4 | 账号id |
| start |  是  |       20200324       |        |
|  end  |  是  |       20200324       |        |

###### 返回正确示例：

```
{
    "data": [
        {
            "account_id": "nYf82sYLNoMT7T8mdvf4",
            "buy_price_mean": 9.38,
            "code": "600520",
            "exchange": "SH",
            "first_buy_date": "20200324",
            "is_clear": 0,
            "last_sell_date": "",
            "max_vol": 958600,
            "profit": -2684.08,
            "pt_symbol": "600520.SH",
            "sell_price_mean": 0.0
        }
    ],
    "status": true
}
```

###### 返回错误示例：

```
{
    "data": "请求参数错误",
    "status": false
}
```

###### 接口测试结果：

- [x] 接口使用正常
