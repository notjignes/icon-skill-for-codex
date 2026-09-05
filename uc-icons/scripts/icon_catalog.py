"""Identity-aware catalog shared by the icon command-line tools."""
from __future__ import annotations
import csv
import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
BASE_MANIFEST = SKILL_DIR / 'references/base-objects/MANIFEST.csv'
SERVICE_MANIFEST = SKILL_DIR / 'references/archive/PNGs_renamed/MANIFEST.csv'
NEW_MANIFEST = SKILL_DIR / 'references/new-object-references/MANIFEST.csv'
MATERIAL_MANIFEST = SKILL_DIR / 'references/archive/PNGs_material_index/MANIFEST.csv'
# Only identity synonyms belong here. Related objects remain separate families.
FAMILIES = {
 'massage-table': ['massage table','massage tables','massage bed','massage beds','spa bed'],
 'table-lamp': ['table lamp','desk lamp'], 'office-chair': ['office chair','desk chair'],
 'salon-chair': ['salon chair','barber chair'], 'armchair': ['armchair','armchairs'],
 'sofa': ['sofa','couch'], 'chair': ['chair','seat'],
 'bedbug': ['bed bug','bed bugs','bedbug','bedbugs'], 'cockroach': ['cockroach','cockroaches'],
 'ant': ['ant'], 'termite': ['termite'], 'air-purifier': ['air purifier'],
 'water-purifier': ['water purifier','native ro','ro purifier','ro'],
 'air-cooler': ['air cooler'], 'air-conditioner': ['air conditioner','split ac','ac unit','ac'],
 'water-heater': ['water heater','geyser'], 'refrigerator': ['refrigerator','fridge'],
 'washing-machine': ['washing machine','washer'], 'microwave': ['microwave'],
 'ceiling-fan': ['ceiling fan'], 'kitchen-chimney': ['kitchen chimney','range hood','chimney hood'],
 'hair-dryer': ['hair dryer','hairdryer'], 'vacuum': ['vacuum cleaner','vacuum'],
 'gift-box': ['gift box','present box'], 'truck': ['box truck','truck'],
 'van': ['van'], 'car': ['car','sedan'], 'bus': ['bus'], 'suitcase': ['suitcase','luggage'],
 'tap': ['basin mixer tap','mixer tap','tap','faucet'], 'sink': ['sink','basin'],
 'cabinet': ['cabinet'], 'shelf': ['shelf cabinet','open shelf','shelf'],
 'dresser': ['dresser','chest of drawers'], 'curtains': ['curtains','curtain'],
 'railing': ['glass balustrade','balustrade','railing'],
 'cooking-pot': ['cooking pot','pot'], 'stove': ['gas stove','stove'],
 'bucket': ['bucket'], 'cleaning-caddy': ['cleaning caddy','caddy'],
 'laundry-basket': ['laundry basket'], 'woven-basket': ['woven basket'],
 'house': ['house model','house'], 'door': ['door'], 'document': ['document','amc paper'],
 'id-card': ['id card'], 'dumbbell': ['dumbbell'], 'laptop': ['laptop'],
 'lipstick': ['lipstick'], 'nail-polish': ['nail polish'], 'lotus': ['lotus'],
 'paint-roller': ['paint roller'], 'smart-lock': ['smart locks','smart lock'],
 'socket-switch': ['socket','switch'], 'television': ['television','tv'],
 'toilet': ['toilet'], 'toolbox': ['toolbox'], 'wall-panel': ['wall panel','wall panels'],
 'crossed-tools': ['wrench screwdriver crossed','wrench and screwdriver','wrench screwdriver'],
 'drill': ['power drill','drill'], 'wrench': ['wrench'], 'screwdriver': ['screwdriver'],
 'lamp': ['standing lamp','floor lamp','lamp'], 'table': ['table'], 'bed': ['bed','cot'],
 'bench': ['bench'], 'wardrobe': ['wardrobe'],
 'charging-station': ['charging station'], 'charger': ['charger'], 'cover': ['cover'],
 'case': ['case'], 'stand': ['stand'], 'holder': ['holder'], 'bottle': ['bottle'], 'bag': ['bag'],
}
COLORS = {'black','white','pink','beige','blue','purple','green','red','yellow','grey','gray','brown','orange'}
MATERIALS = {'wood','wooden','metal','steel','chrome','glass','ceramic','enamel','rubber','silicone','leather','velvet','fabric','woven','rattan','plastic','stone','granite','marble','plaster','paper'}
APPROVED = {'approved','existing_curated'}
COMPOSITIONS = ('front','wide-side','slight-top','three-quarter','crossed-pair')


def normalize(value: str) -> str:
    return ' '.join(re.findall(r'[a-z0-9]+', value.lower()))


def words(value: str) -> set[str]:
    return set(normalize(value).split())


def has_phrase(value: str, phrase: str) -> bool:
    return f' {normalize(phrase)} ' in f' {normalize(value)} '


def read_manifest(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(newline='', encoding='utf-8-sig') as handle:
        return list(csv.DictReader(handle))


def resolve_path(row: dict, folder: Path, key: str) -> Path | None:
    alias = row.get('image_path', '').strip()
    candidate = (SKILL_DIR / alias if alias else folder / row.get(key, '')).resolve()
    if not candidate.is_relative_to(SKILL_DIR.resolve()) or not candidate.is_file():
        return None
    return candidate


def load_assets(manifest: Path, key: str) -> list[dict]:
    result = []
    for row in read_manifest(manifest):
        default = 'pending' if manifest == NEW_MANIFEST else 'existing_curated'
        if row.get('approval_status', default) not in APPROVED:
            continue
        path = resolve_path(row, manifest.parent, key)
        if path is not None and row.get(key):
            result.append({**row, 'file': row[key], 'path': str(path)})
    return result


def bases() -> list[dict]:
    return load_assets(BASE_MANIFEST, 'base_file')


def services() -> list[dict]:
    return load_assets(SERVICE_MANIFEST, 'service_file')


def family(subject: str) -> str:
    subject = re.split(r'\b(?:with|carrying|holding)\b', normalize(subject), maxsplit=1)[0]
    def rank(alias: str, key: str) -> list[tuple]:
        phrase = normalize(alias)
        return [(m.end(),len(phrase),key) for m in re.finditer(r'(?<![a-z0-9])'+re.escape(phrase)+r'(?![a-z0-9])', subject)]
    matches = [match for key, aliases in FAMILIES.items() for alias in aliases for match in rank(alias,key)]
    # Intake can teach a new identity without editing Python.
    for row in load_assets(NEW_MANIFEST, 'reference_file'):
        key = row.get('object_family', '').strip()
        if key:
            for alias in [key, *row.get('identity_aliases', '').split(';')]:
                if alias.strip() and has_phrase(subject, alias):
                    matches.extend(rank(alias,key))
    return max(matches, default=(0, 0, ''))[2]


def base_family(row: dict) -> str:
    if row.get('type') == 'human':
        return 'human'
    name = normalize(Path(row['file']).stem).split(' with ')[0]
    return row.get('object_family') or family(name)


def is_human(subject: str) -> bool:
    primary = re.split(r'\b(?:with|carrying|holding)\b', normalize(subject), maxsplit=1)[0]
    identity = family(primary)
    aliases = FAMILIES.get(identity, [identity] if identity else [])
    object_end = max((m.end() for a in aliases for m in re.finditer(r'(?<![a-z0-9])'+re.escape(normalize(a))+r'(?![a-z0-9])',primary)), default=0)
    human_terms = {'female','male','woman','women','man','men','maid','helper','chef','cook','technician','guard','driver','trainer','nurse','therapist','client','salon','spa','massage','cleaner','attendant'}
    human_end = max((m.end() for m in re.finditer(r'\b[a-z]+\b',primary) if m.group() in human_terms), default=0)
    return human_end > object_end


def default_orientation(subject: str) -> str:
    if family(subject) in {'massage-table','van','truck','car','bus','sofa','bed','bench','table','curtains','railing'}:
        return 'side-horizontal'
    return 'front-near-orthographic'


def composition_orientation(composition: str) -> str:
    return {'front':'front-near-orthographic','wide-side':'side-horizontal','slight-top':'front-slight-top','three-quarter':'three-quarter','crossed-pair':'crossed-pair'}[composition]


def orientation_prompt(orientation: str) -> str:
    return {
      'side-horizontal':'side-horizontal straight profile, long axis level, no angled perspective or top-down view',
      'front-slight-top':'straight front view with slight top-face visibility only for recognition',
      'three-quarter':'controlled three-quarter view, near-orthographic, full subject visible',
      'crossed-pair':'flat front-readable crossed pair, one coherent silhouette, no perspective scene',
      'front-bust':'straight front-facing UC character bust, preserve canonical crop and optical size',
    }.get(orientation, 'straight front view, near-orthographic, no three-quarter or top-down view')


def choose_bases(subject: str) -> list[dict]:
    identity = family(subject)
    if not identity:
        return []
    candidates = [r for r in bases() if base_family(r) == identity]
    primary = re.split(r'\b(?:with|carrying|holding)\b',normalize(subject),maxsplit=1)[0]
    query = words(primary)
    # Unknown qualifiers can change object identity ('car charging station').
    # Reuse is allowed only when the supplied subject is explained by the alias
    # and known object metadata. Full unknown subjects proceed to new generation.
    identity_words = set().union(*(words(a) for a in FAMILIES.get(identity, [identity])))
    harmless = COLORS | MATERIALS | {'a','an','the','normal','regular','single','pair','two','couples','couple','transportation','transport'}
    candidates = [r for r in candidates if query <= (identity_words | harmless | words(r['file']+' '+r.get('objects','')+' '+r.get('colors','')))]
    pair = bool(query & {'pair','two','couples','couple'})
    candidates = [r for r in candidates if bool(words(r['file']) & {'pair','two'}) == pair]
    if identity == 'water-purifier':
        if 'native' in query:
            candidates = [r for r in candidates if 'native' in words(r['file'])]
        elif query & {'normal','regular','wall','repair'}:
            candidates = [r for r in candidates if 'native' not in words(r['file'])]
    color_matches = [r for r in candidates if query & COLORS & words(r.get('colors','')+' '+r['file'])]
    if color_matches:
        candidates = color_matches
    exact = [r for r in candidates if normalize(Path(r['file']).stem) == normalize(subject)]
    return sorted(exact or candidates, key=lambda r: r['file'].lower())
