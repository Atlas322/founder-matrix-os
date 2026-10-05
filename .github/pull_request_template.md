## Юу өөрчилсөн бэ

<!-- 1–3 өгүүлбэр. Ямар skill / script / баримт. -->

## Яагаад

<!-- Ямар асуудлыг шийдэж байна. Issue байвал: Closes #123 -->

## Хэрхэн тестэлсэн

- [ ] `python3 tests/test_hooks.py`
- [ ] `python3 tests/test_onboard.py`
- [ ] `python3 tools/relay/tests/test_relay_config.py`
- [ ] `claude plugin validate --strict plugins/fm`
- [ ] Туршилтын (жинхэнэ биш) vault дээр гараар шалгасан: <!-- юуг -->

OS: <!-- macOS / Windows / Linux -->  Python: <!-- python3 --version -->

## Шалгах жагсаалт

- [ ] Vault-ийн агуулга, token, нууц үг, харилцагчийн мэдээлэл, хувийн зам **ороогүй** (`git diff`-ээ харсан)
- [ ] Python 3.9-д ажиллана, цэвэр Python (bash/jq/pip сан шаардахгүй), Windows дээр ажиллана
- [ ] Хэрэглэгчид харагдах текст монголоор, skill/файлын нэр англи kebab-case
- [ ] Файлын мөрийн төгсгөлийг (LF/CRLF) өөрчлөөгүй
- [ ] Хувийн зүйл (finance, `private: true`) vault-аас гарахгүй хэвээр
- [ ] Шаардлагатай бол README / CHANGELOG шинэчилсэн
- [ ] `plugin.json`-ийн `version`-ийг өөрчлөөгүй (itge.e гаргахдаа нэмнэ)

PR илгээснээр энэ хувь нэмрийг repo-ийн [LICENSE](../LICENSE)-ийн нөхцлөөр itge.e-д лицензлэж байгаагаа зөвшөөрч байна.
