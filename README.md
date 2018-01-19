pyramid_oas3
============

[Pyramid](https://trypyramid.com/) Webアプリケーションに対して、
[OpenAPI](https://www.openapis.org/) [3.0](https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md)を利用した、
リクエストの検証・パースを実施するライブラリです。

[pyramid_swagger](https://github.com/striglia/pyramid_swagger)のOpenAPI 3.0対応版の様な位置づけです。

設定項目
--------

* pyramid_oas3.validate_response: [bool] レスポンスのJSONも検証するかを設定します(デフォルト: False)
* pyramid_oas3.fill_by_default: [bool] リクエストデータに対してOpenAPI定義で設定されたdefault値で埋めるかを設定します(デフォルト: False)


使い方
------

以下のように設定してpyramidに組み込みます

```
settings = {
    'pyramid.includes': 'pyramid_oas3',
    'pyramid_oas3.schema': yaml.load(open('schema.yaml').read()),
    'pyramid_oas3.validate_response': True,
    'pyramid_oas3.fill_by_default': True,
}
```

検証失敗時は以下の例外が返却されるので、
適宜exception_view_configを設定してください

* pyramid_oas3.ValidationErrors: リクエストデータのスキーマ検証失敗時
* pyramid_oas3.ResponseValidationError: レスポンスデータのスキーマ検証失敗時
* pyramid.httpexceptions.HTTPBadRequest: クエリ文字列のパース失敗時
* pyramid.httpexceptions.HTTPNotAcceptable: リクエストのContentTypeに対応するものがスキーマにない
＊pyramid.httpexceptions.HTTPUnauthorized: リクエストに認証情報がない

以下にexception_view_configの例を示します

```
from pyramid.view import exception_view_config


@exception_view_config(ValidationErrors)
def failed_request_validation(exc, request):
    res = Response(str(exc))
    res.status_int = 400
    return res


@exception_view_config(ResponseValidationError)
def failed_response_validation(exc, request):
    res = Response(str(exc))
    res.status_int = 500
    return res
```
