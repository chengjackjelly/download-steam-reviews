from easysteam import get_steam_api_url


def test_get_steam_api_url() -> None:
    assert isinstance(get_steam_api_url("814380"),str)
