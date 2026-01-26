


# src/geo/plz_registry.py

from typing import Dict, Tuple

# EINZIGE Quelle für PLZ → Koordinaten

PLZ_TO_LATLON: Dict[str, Tuple[float, float]] = {
"1020": (48.2064, 16.4328),
"1030": (48.1995, 16.3923),
"1050": (48.1873, 16.3560),
"1070": (48.2035, 16.3559),
"1080": (48.2108, 16.3443),
"1090": (48.2284, 16.3625),
"1100": (48.1760, 16.3688),
"1110": (48.1697, 16.4252),
"1120": (48.1803, 16.3314),
"1130": (48.1730, 16.2784),
"1140": (48.2048, 16.2638),
"1150": (48.1947, 16.3272),
"1160": (48.2189, 16.2953),
"1210": (48.2679, 16.3846),
"1220": (48.2152, 16.4841),
"1230": (48.2145, 16.5237),

"3400": (48.3053, 16.3257),   # Klosterneuburg
"8020": (47.0713, 15.4280),   # Graz

"5020": (47.8095, 13.0550),   # Salzburg
"5023": (47.8330, 13.0700),   # Salzburg-Gnigl
"5026": (47.7710, 13.0660),   # Salzburg-Aigen
"5161": (47.9390, 12.9540),   # Elixhausen
"5325": (47.7500, 13.3500),   # Plainfeld
"5400": (47.6841, 13.0995),   # Hallein
"5573": (47.2000, 13.6800),   # Weißpriach

"4522": (48.0500, 14.2500),   # Sierning
"4542": (48.0330, 14.1830),   # Nußbach
"4550": (48.0420, 14.2140),   # Kremsmünster
"4560": (48.0730, 14.2680),   # Kirchdorf an der Krems
"4563": (48.0300, 14.3000),   # Micheldorf
"4800": (48.0040, 13.6560),   # Attnang-Puchheim

"2224": (48.4100, 16.7200),   # Obersdorf
"9238": (46.6300, 14.3000),   # Bad Eisenkappel Umgebung
"9524": (46.6200, 13.9200),   # Villach-Land Umgebung


# Wien
"1030": (48.1987, 16.3946),   # Wien-Landstraße
"1170": (48.2333, 16.3167),   # Wien-Hernals
"1210": (48.2833, 16.4167),   # Wien-Floridsdorf
"1220": (48.2333, 16.5000),   # Wien-Donaustadt

# Niederösterreich
"2700": (47.8167, 16.2500),   # Wiener Neustadt

# Kärnten
"9100": (46.6247, 14.3053),   # Völkermarkt
"9112": (46.6380, 14.3830),   # Griffen
"9150": (46.5514, 14.2711),   # Bleiburg
"9634": (46.6369, 13.0492),   # Gundersheim (Bez. Hermagor)

}



# Regel

#neue PLZ → hier ergänzen

#niemals dynamisch ändern

#Git-Versionierung = Audit-Trail