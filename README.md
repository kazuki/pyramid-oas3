pyramid_oas3
============

[Pyramid](https://trypyramid.com/) Webアプリケーションに対して、
[OpenAPI](https://www.openapis.org/) [3.0](https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md)を利用した、
リクエストの検証・パースを実施するライブラリです。

[pyramid_swagger](https://github.com/striglia/pyramid_swagger)のOpenAPI 3.0対応版の様な位置づけです。

設定項目
--------

* pyramid_oas3.validate_response[bool]: レスポンスのJSONも検証するかを設定します
* pyramid_oas3.fill_by_default[bool]: リクエストデータに対してOpenAPI定義で設定されたdefault値で埋めるかを設定します
* pyramid_oas3.validation_context_path[str]: スキーマ検証エラー発生時に任意の処理を行なう関数を設定します
