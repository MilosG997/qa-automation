"""Legal and install basics on my sites: privacy pages that name the analytics tool, web app manifests that work."""
import pytest

from helpers import http

PRIVACY = {
    "mg-sr": ("https://mechanicallygifted.rs/privatnost/", "Politika privatnosti"),
    "mg-en": ("https://mechanicallygifted.rs/en/privacy/", "Privacy policy"),
    "draganic": ("https://draganicstolarija.rs/politika-privatnosti/", "Politika privatnosti"),
    "majstori": ("https://majstoripazova.rs/privatnost", "Politika privatnosti"),
}
MANIFESTS = {
    "mg": "https://mechanicallygifted.rs/site.webmanifest",
    "draganic": "https://draganicstolarija.rs/site.webmanifest",
    "majstori": "https://majstoripazova.rs/manifest.webmanifest",
}


@pytest.mark.parametrize("name", PRIVACY)
def test_privacy_page_exists_and_has_a_title(name):
    url, title = PRIVACY[name]
    response = http.get(url, timeout=20)
    assert response.status_code == 200
    assert f">{title}</h1>" in response.text


@pytest.mark.parametrize("name", ["mg-sr", "mg-en", "majstori"])
def test_privacy_page_names_google_analytics(name):
    """Sites that use Google Analytics must say so in the privacy policy."""
    assert "Google Analytics" in http.get(PRIVACY[name][0], timeout=20).text


@pytest.mark.parametrize("name", ["mg-sr", "mg-en"])
def test_privacy_page_gives_a_contact(name):
    assert "mechanicallygifted@gmail.com" in http.get(PRIVACY[name][0], timeout=20).text


@pytest.mark.parametrize("name", MANIFESTS)
def test_manifest_has_name_start_url_and_colors(name):
    manifest = http.get(MANIFESTS[name], timeout=20).json()
    assert manifest["name"] and manifest["short_name"]
    assert manifest["start_url"] == "/"
    assert manifest["theme_color"].startswith("#") and manifest["background_color"].startswith("#")


@pytest.mark.parametrize("name", MANIFESTS)
def test_manifest_icons_are_served(name):
    base = MANIFESTS[name].rsplit("/", 1)[0]
    icons = http.get(MANIFESTS[name], timeout=20).json()["icons"]
    assert {"192x192", "512x512"} <= {i.get("sizes") for i in icons}
    for icon in icons:
        response = http.head(base + icon["src"], timeout=20)
        assert response.status_code == 200, icon["src"]
        assert response.headers["Content-Type"].startswith("image/")
