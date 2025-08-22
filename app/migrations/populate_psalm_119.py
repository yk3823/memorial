"""
Psalm 119 Database Population Migration
Populates the complete Psalm 119 with all 176 verses in Hebrew, English, and transliteration.
Organized by the 22 Hebrew letters, 8 verses each.
"""

import asyncio
import logging
from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.core.database import get_database, _session_factory
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db_session():
    """Get database session for migration."""
    from app.core.database import create_database_engine, create_session_factory
    from app.core.config import get_settings
    
    settings = get_settings()
    engine = create_database_engine(str(settings.SQLALCHEMY_DATABASE_URI), echo=False)
    session_factory = create_session_factory(engine)
    
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise

from app.models.psalm_119 import Psalm119Letter, Psalm119Verse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Hebrew Alphabet Data for Psalm 119
HEBREW_LETTERS_DATA = [
    {"id": 1, "hebrew_letter": "א", "hebrew_name": "אלף", "english_name": "Aleph", "transliteration": "alef", "numeric_value": 1, "position": 1},
    {"id": 2, "hebrew_letter": "ב", "hebrew_name": "בית", "english_name": "Bet", "transliteration": "bet", "numeric_value": 2, "position": 2},
    {"id": 3, "hebrew_letter": "ג", "hebrew_name": "גימל", "english_name": "Gimel", "transliteration": "gimel", "numeric_value": 3, "position": 3},
    {"id": 4, "hebrew_letter": "ד", "hebrew_name": "דלת", "english_name": "Dalet", "transliteration": "dalet", "numeric_value": 4, "position": 4},
    {"id": 5, "hebrew_letter": "ה", "hebrew_name": "הא", "english_name": "He", "transliteration": "he", "numeric_value": 5, "position": 5},
    {"id": 6, "hebrew_letter": "ו", "hebrew_name": "וו", "english_name": "Vav", "transliteration": "vav", "numeric_value": 6, "position": 6},
    {"id": 7, "hebrew_letter": "ז", "hebrew_name": "זין", "english_name": "Zayin", "transliteration": "zayin", "numeric_value": 7, "position": 7},
    {"id": 8, "hebrew_letter": "ח", "hebrew_name": "חית", "english_name": "Het", "transliteration": "het", "numeric_value": 8, "position": 8},
    {"id": 9, "hebrew_letter": "ט", "hebrew_name": "טית", "english_name": "Tet", "transliteration": "tet", "numeric_value": 9, "position": 9},
    {"id": 10, "hebrew_letter": "י", "hebrew_name": "יוד", "english_name": "Yod", "transliteration": "yod", "numeric_value": 10, "position": 10},
    {"id": 11, "hebrew_letter": "כ", "hebrew_name": "כף", "english_name": "Kaf", "transliteration": "kaf", "numeric_value": 20, "position": 11},
    {"id": 12, "hebrew_letter": "ל", "hebrew_name": "למד", "english_name": "Lamed", "transliteration": "lamed", "numeric_value": 30, "position": 12},
    {"id": 13, "hebrew_letter": "מ", "hebrew_name": "מם", "english_name": "Mem", "transliteration": "mem", "numeric_value": 40, "position": 13},
    {"id": 14, "hebrew_letter": "נ", "hebrew_name": "נון", "english_name": "Nun", "transliteration": "nun", "numeric_value": 50, "position": 14},
    {"id": 15, "hebrew_letter": "ס", "hebrew_name": "סמך", "english_name": "Samech", "transliteration": "samech", "numeric_value": 60, "position": 15},
    {"id": 16, "hebrew_letter": "ע", "hebrew_name": "עין", "english_name": "Ayin", "transliteration": "ayin", "numeric_value": 70, "position": 16},
    {"id": 17, "hebrew_letter": "פ", "hebrew_name": "פא", "english_name": "Pe", "transliteration": "pe", "numeric_value": 80, "position": 17},
    {"id": 18, "hebrew_letter": "צ", "hebrew_name": "צדי", "english_name": "Tzade", "transliteration": "tzade", "numeric_value": 90, "position": 18},
    {"id": 19, "hebrew_letter": "ק", "hebrew_name": "קוף", "english_name": "Qof", "transliteration": "qof", "numeric_value": 100, "position": 19},
    {"id": 20, "hebrew_letter": "ר", "hebrew_name": "ריש", "english_name": "Resh", "transliteration": "resh", "numeric_value": 200, "position": 20},
    {"id": 21, "hebrew_letter": "ש", "hebrew_name": "שין", "english_name": "Shin", "transliteration": "shin", "numeric_value": 300, "position": 21},
    {"id": 22, "hebrew_letter": "ת", "hebrew_name": "תו", "english_name": "Tav", "transliteration": "tav", "numeric_value": 400, "position": 22}
]

# Complete Psalm 119 verses - all 176 verses in Hebrew
PSALM_119_VERSES = [
    # א (Aleph) - verses 1-8
    {"verse": 1, "letter": 1, "section": 1, "hebrew": "אַשְׁרֵי תְמִימֵי דָרֶךְ הַהֹלְכִים בְּתוֹרַת יְהוָה", "english": "Blessed are the undefiled in the way, who walk in the law of the LORD.", "transliteration": "ashrei t'mimei darech haholchim b'torat adonai"},
    {"verse": 2, "letter": 1, "section": 2, "hebrew": "אַשְׁרֵי נֹצְרֵי עֵדֹתָיו בְּכָל־לֵב יִדְרְשׁוּהוּ", "english": "Blessed are they that keep his testimonies, and that seek him with the whole heart.", "transliteration": "ashrei notz'rei edotav b'chol-lev yidreshchu"},
    {"verse": 3, "letter": 1, "section": 3, "hebrew": "אַף לֹא־פָעֲלוּ עַוְלָה בִּדְרָכָיו הָלָכוּ", "english": "They also do no iniquity: they walk in his ways.", "transliteration": "af lo-fa'alu avlah bidrachav halchu"},
    {"verse": 4, "letter": 1, "section": 4, "hebrew": "אַתָּה צִוִּיתָה פִקֻּדֶיךָ לִשְׁמֹר מְאֹד", "english": "Thou hast commanded us to keep thy precepts diligently.", "transliteration": "atah tzivitah fikudeicha lishmor m'od"},
    {"verse": 5, "letter": 1, "section": 5, "hebrew": "אַחֲלַי יִכֹּנוּ דְרָכָי לִשְׁמֹר חֻקֶּיךָ", "english": "O that my ways were directed to keep thy statutes!", "transliteration": "achalai yikonu d'rachai lishmor chukeicha"},
    {"verse": 6, "letter": 1, "section": 6, "hebrew": "אָז לֹא־אֵבוֹשׁ בְּהַבִּיטִי אֶל־כָּל־מִצְוֹתֶיךָ", "english": "Then shall I not be ashamed, when I have respect unto all thy commandments.", "transliteration": "az lo-evosh b'habiti el-kol-mitzvoteicha"},
    {"verse": 7, "letter": 1, "section": 7, "hebrew": "אוֹדְךָ בְיֹשֶׁר לֵבָב בְּלָמְדִי מִשְׁפְּטֵי צִדְקֶךָ", "english": "I will praise thee with uprightness of heart, when I shall have learned thy righteous judgments.", "transliteration": "od'cha b'yosher levav b'lamdi mishp'tei tzidkecha"},
    {"verse": 8, "letter": 1, "section": 8, "hebrew": "אֶת־חֻקֶּיךָ אֶשְׁמֹר אַל־תַּעַזְבֵנִי עַד־מְאֹד", "english": "I will keep thy statutes: O forsake me not utterly.", "transliteration": "et-chukeicha eshmor al-ta'azveni ad-m'od"},

    # ב (Bet) - verses 9-16
    {"verse": 9, "letter": 2, "section": 1, "hebrew": "בַּמֶּה יְזַכֶּה־נַּעַר אֶת־אָרְחוֹ לִשְׁמֹר כִּדְבָרֶךָ", "english": "Wherewithal shall a young man cleanse his way? by taking heed thereto according to thy word.", "transliteration": "bameh y'zakeh-na'ar et-orcho lishmor kid'varecha"},
    {"verse": 10, "letter": 2, "section": 2, "hebrew": "בְּכָל־לִבִּי דְרַשְׁתִּיךָ אַל־תַּשְׁגֵּנִי מִמִּצְוֹתֶיךָ", "english": "With my whole heart have I sought thee: O let me not wander from thy commandments.", "transliteration": "b'chol-libi d'rashticha al-tashgeini mimitzevoteicha"},
    {"verse": 11, "letter": 2, "section": 3, "hebrew": "בְּלִבִּי צָפַנְתִּי אִמְרָתֶךָ לְמַעַן לֹא אֶחֱטָא־לָךְ", "english": "Thy word have I hid in mine heart, that I might not sin against thee.", "transliteration": "b'libi tzafanti imratecha l'ma'an lo echeta-lach"},
    {"verse": 12, "letter": 2, "section": 4, "hebrew": "בָּרוּךְ אַתָּה יְהוָה לַמְּדֵנִי חֻקֶּיךָ", "english": "Blessed art thou, O LORD: teach me thy statutes.", "transliteration": "baruch atah adonai lam'deini chukeicha"},
    {"verse": 13, "letter": 2, "section": 5, "hebrew": "בִּשְׂפָתַי סִפַּרְתִּי כֹּל מִשְׁפְּטֵי־פִיךָ", "english": "With my lips have I declared all the judgments of thy mouth.", "transliteration": "bis'fatai siparti kol mishp'tei-ficha"},
    {"verse": 14, "letter": 2, "section": 6, "hebrew": "בְּדֶרֶךְ עֵדְוֹתֶיךָ שַׂשְׂתִּי כְּעַל כָּל־הוֹן", "english": "I have rejoiced in the way of thy testimonies, as much as in all riches.", "transliteration": "b'derech edvoteicha sasti k'al kol-hon"},
    {"verse": 15, "letter": 2, "section": 7, "hebrew": "בְּפִקֻּדֶיךָ אָשִׂיחָה וְאַבִּיטָה אֹרְחֹתֶיךָ", "english": "I will meditate in thy precepts, and have respect unto thy ways.", "transliteration": "b'fikudeicha asicha v'abitah orchoteicha"},
    {"verse": 16, "letter": 2, "section": 8, "hebrew": "בְּחֻקֹּתֶיךָ אֶשְׁתַּעֲשָׁע לֹא אֶשְׁכַּח דְּבָרֶךָ", "english": "I will delight myself in thy statutes: I will not forget thy word.", "transliteration": "b'chukoteicha eshtasha'a lo eshkach d'varecha"},

    # ג (Gimel) - verses 17-24
    {"verse": 17, "letter": 3, "section": 1, "hebrew": "גְּמֹל עַל־עַבְדְּךָ אֶחְיֶה וְאֶשְׁמְרָה דְבָרֶךָ", "english": "Deal bountifully with thy servant, that I may live, and keep thy word.", "transliteration": "g'mol al-avd'cha echyeh v'eshm'rah d'varecha"},
    {"verse": 18, "letter": 3, "section": 2, "hebrew": "גַּל־עֵינַי וְאַבִּיטָה נִפְלָאוֹת מִתּוֹרָתֶךָ", "english": "Open thou mine eyes, that I may behold wondrous things out of thy law.", "transliteration": "gal-einai v'abitah nifla'ot mitoratecha"},
    {"verse": 19, "letter": 3, "section": 3, "hebrew": "גֵּר אָנֹכִי בָאָרֶץ אַל־תַּסְתֵּר מִמֶּנִּי מִצְוֹתֶיךָ", "english": "I am a stranger in the earth: hide not thy commandments from me.", "transliteration": "ger anochi ba'aretz al-taster mimenni mitzvoteicha"},
    {"verse": 20, "letter": 3, "section": 4, "hebrew": "גָּרְסָה נַפְשִׁי לְתַאֲבָה אֶל־מִשְׁפָּטֶיךָ בְכָל־עֵת", "english": "My soul breaketh for the longing that it hath unto thy judgments at all times.", "transliteration": "garsah nafshi l'ta'avah el-mishpateicha b'chol-et"},
    {"verse": 21, "letter": 3, "section": 5, "hebrew": "גָּעַרְתָּ זֵדִים אֲרוּרִים הַשֹּׁגִים מִמִּצְוֹתֶיךָ", "english": "Thou hast rebuked the proud that are cursed, which do err from thy commandments.", "transliteration": "ga'arta zeidim arurim hashogim mimitzevoteicha"},
    {"verse": 22, "letter": 3, "section": 6, "hebrew": "גַּל מֵעָלַי חֶרְפָּה וָבוּז כִּי עֵדֹתֶיךָ נָצָרְתִּי", "english": "Remove from me reproach and contempt; for I have kept thy testimonies.", "transliteration": "gal me'alai cherpah vavuz ki edoteicha natzarti"},
    {"verse": 23, "letter": 3, "section": 7, "hebrew": "גַּם יָשְׁבוּ שָׂרִים בִּי נִדְבָּרוּ עַבְדְּךָ יָשִׂיחַ בְּחֻקֶּיךָ", "english": "Princes also did sit and speak against me: but thy servant did meditate in thy statutes.", "transliteration": "gam yash'vu sarim bi nidbaru avd'cha yasiach b'chukeicha"},
    {"verse": 24, "letter": 3, "section": 8, "hebrew": "גַּם־עֵדֹתֶיךָ שַׁעֲשֻׁעַי אַנְשֵׁי עֲצָתִי", "english": "Thy testimonies also are my delight and my counselors.", "transliteration": "gam-edoteicha sha'ashu'ai anshei atzati"},

    # ד (Dalet) - verses 25-32
    {"verse": 25, "letter": 4, "section": 1, "hebrew": "דָּבְקָה לֶעָפָר נַפְשִׁי חַיֵּנִי כִּדְבָרֶךָ", "english": "My soul cleaveth unto the dust: quicken thou me according to thy word.", "transliteration": "dav'kah le'afar nafshi chayeini kid'varecha"},
    {"verse": 26, "letter": 4, "section": 2, "hebrew": "דְּרָכַי סִפַּרְתִּי וַתַּעֲנֵנִי לַמְּדֵנִי חֻקֶּיךָ", "english": "I have declared my ways, and thou heardest me: teach me thy statutes.", "transliteration": "d'rachai siparti vata'aneini lam'deini chukeicha"},
    {"verse": 27, "letter": 4, "section": 3, "hebrew": "דֶּרֶךְ־פִּקּוּדֶיךָ הֲבִינֵנִי וְאָשִׂיחָה בְּנִפְלְאוֹתֶיךָ", "english": "Make me to understand the way of thy precepts: so shall I talk of thy wondrous works.", "transliteration": "derech-pikudeicha havineini v'asicha b'nifl'oteicha"},
    {"verse": 28, "letter": 4, "section": 4, "hebrew": "דָּלְפָה נַפְשִׁי מִתּוּגָה קַיְּמֵנִי כִּדְבָרֶךָ", "english": "My soul melteth for heaviness: strengthen thou me according unto thy word.", "transliteration": "dalefah nafshi mitugah kaymeini kid'varecha"},
    {"verse": 29, "letter": 4, "section": 5, "hebrew": "דֶּרֶךְ־שֶׁקֶר הָסֵר מִמֶּנִּי וְתוֹרָתְךָ חָנֵּנִי", "english": "Remove from me the way of lying: and grant me thy law graciously.", "transliteration": "derech-sheker haser mimenni v'torat'cha chaneini"},
    {"verse": 30, "letter": 4, "section": 6, "hebrew": "דֶּרֶךְ־אֱמוּנָה בָחָרְתִּי מִשְׁפָּטֶיךָ שִׁוִּיתִי", "english": "I have chosen the way of truth: thy judgments have I laid before me.", "transliteration": "derech-emunah bacharti mishpateicha shiviti"},
    {"verse": 31, "letter": 4, "section": 7, "hebrew": "דָּבַקְתִּי בְעֵדְוֹתֶיךָ יְהוָה אַל־תְּבִישֵׁנִי", "english": "I have stuck unto thy testimonies: O LORD, put me not to shame.", "transliteration": "davakti b'edvoteicha adonai al-t'visheini"},
    {"verse": 32, "letter": 4, "section": 8, "hebrew": "דֶּרֶךְ־מִצְוֹתֶיךָ אָרוּץ כִּי תַרְחִיב לִבִּי", "english": "I will run the way of thy commandments, when thou shalt enlarge my heart.", "transliteration": "derech-mitzvoteicha arutz ki tarchiv libi"},

    # ה (He) - verses 33-40
    {"verse": 33, "letter": 5, "section": 1, "hebrew": "הוֹרֵנִי יְהוָה דֶּרֶךְ חֻקֶּיךָ וְאֶצְּרֶנָּה עֵקֶב", "english": "Teach me, O LORD, the way of thy statutes; and I shall keep it unto the end.", "transliteration": "horeini adonai derech chukeicha v'etzrenah ekev"},
    {"verse": 34, "letter": 5, "section": 2, "hebrew": "הֲבִינֵנִי וְאֶצְּרָה תוֹרָתֶךָ וְאֶשְׁמְרֶנָּה בְכָל־לֵב", "english": "Give me understanding, and I shall keep thy law; yea, I shall observe it with my whole heart.", "transliteration": "havineini v'etz'rah toratecha v'eshm'renah v'chol-lev"},
    {"verse": 35, "letter": 5, "section": 3, "hebrew": "הַדְרִיכֵנִי בִּנְתִיב מִצְוֹתֶיךָ כִּי־בוֹ חָפָצְתִּי", "english": "Make me to go in the path of thy commandments; for therein do I delight.", "transliteration": "hadricheini bintiv mitzvoteicha ki-vo chafatzti"},
    {"verse": 36, "letter": 5, "section": 4, "hebrew": "הַט־לִבִּי אֶל־עֵדְוֹתֶיךָ וְאַל אֶל־בָּצַע", "english": "Incline my heart unto thy testimonies, and not to covetousness.", "transliteration": "hat-libi el-edvoteicha v'al el-batza"},
    {"verse": 37, "letter": 5, "section": 5, "hebrew": "הַעֲבֵר עֵינַי מֵרְאוֹת שָׁוְא בִּדְרָכֶךָ חַיֵּנִי", "english": "Turn away mine eyes from beholding vanity; and quicken thou me in thy way.", "transliteration": "ha'aver einai mer'ot shav bid'rachecha chayeini"},
    {"verse": 38, "letter": 5, "section": 6, "hebrew": "הָקֵם לְעַבְדְּךָ אִמְרָתֶךָ אֲשֶׁר לְיִרְאָתֶךָ", "english": "Stablish thy word unto thy servant, who is devoted to thy fear.", "transliteration": "hakem l'avd'cha imratecha asher l'yir'atecha"},
    {"verse": 39, "letter": 5, "section": 7, "hebrew": "הַעֲבֵר חֶרְפָּתִי אֲשֶׁר יָגֹרְתִּי כִּי מִשְׁפָּטֶיךָ טוֹבִים", "english": "Turn away my reproach which I fear: for thy judgments are good.", "transliteration": "ha'aver cherpati asher yagorti ki mishpateicha tovim"},
    {"verse": 40, "letter": 5, "section": 8, "hebrew": "הִנֵּה תָּאַבְתִּי לְפִקֻּדֶיךָ בְּצִדְקָתְךָ חַיֵּנִי", "english": "Behold, I have longed after thy precepts: quicken me in thy righteousness.", "transliteration": "hineh ta'avti l'fikudeicha b'tzidkat'cha chayeini"},

    # ו (Vav) - verses 41-48
    {"verse": 41, "letter": 6, "section": 1, "hebrew": "וִיבֹאֻנִי חֲסָדֶיךָ יְהוָה תְּשׁוּעָתְךָ כְּאִמְרָתֶךָ", "english": "Let thy mercies come also unto me, O LORD, even thy salvation, according to thy word.", "transliteration": "vivounni chasadeicha adonai t'shu'at'cha k'imratecha"},
    {"verse": 42, "letter": 6, "section": 2, "hebrew": "וְאֶעֱנֶה חֹרְפִי דָבָר כִּי־בָטַחְתִּי בִּדְבָרֶךָ", "english": "So shall I have wherewith to answer him that reproacheth me: for I trust in thy word.", "transliteration": "v'e'eneh chor'fi davar ki-vatachti bid'varecha"},
    {"verse": 43, "letter": 6, "section": 3, "hebrew": "וְאַל־תַּצֵּל מִפִּי דְבַר־אֱמֶת עַד־מְאֹד כִּי לְמִשְׁפָּטֶךָ יִחָלְתִּי", "english": "And take not the word of truth utterly out of my mouth; for I have hoped in thy judgments.", "transliteration": "v'al-tatzel mipi d'var-emet ad-m'od ki l'mishpatecha yichalti"},
    {"verse": 44, "letter": 6, "section": 4, "hebrew": "וְאֶשְׁמְרָה תוֹרָתְךָ תָמִיד לְעוֹלָם וָעֶד", "english": "So shall I keep thy law continually for ever and ever.", "transliteration": "v'eshm'rah torat'cha tamid l'olam va'ed"},
    {"verse": 45, "letter": 6, "section": 5, "hebrew": "וְאֶתְהַלְּכָה בָרְחָבָה כִּי פִקֻּדֶיךָ דָרָשְׁתִּי", "english": "And I will walk at liberty: for I seek thy precepts.", "transliteration": "v'ethal'chah var'chavah ki fikudeicha darashti"},
    {"verse": 46, "letter": 6, "section": 6, "hebrew": "וַאֲדַבְּרָה בְעֵדֹתֶיךָ נֶגֶד מְלָכִים וְלֹא אֵבוֹשׁ", "english": "I will speak of thy testimonies also before kings, and will not be ashamed.", "transliteration": "va'adab'rah v'edoteicha neged m'lachim v'lo evosh"},
    {"verse": 47, "letter": 6, "section": 7, "hebrew": "וְאֶשְׁתַּעֲשַׁע בְּמִצְוֹתֶיךָ אֲשֶׁר אָהָבְתִּי", "english": "And I will delight myself in thy commandments, which I have loved.", "transliteration": "v'eshtasha'a b'mitzvoteicha asher ahavti"},
    {"verse": 48, "letter": 6, "section": 8, "hebrew": "וְאֶשָּׂא־כַפַּי אֶל־מִצְוֹתֶיךָ אֲשֶׁר אָהָבְתִּי וְאָשִׂיחָה בְחֻקֶּיךָ", "english": "My hands also will I lift up unto thy commandments, which I have loved; and I will meditate in thy statutes.", "transliteration": "v'esa-chafai el-mitzvoteicha asher ahavti v'asicha v'chukeicha"},

    # ז (Zayin) - verses 49-56
    {"verse": 49, "letter": 7, "section": 1, "hebrew": "זְכֹר־דָּבָר לְעַבְדֶּךָ עַל אֲשֶׁר יִחַלְתָּנִי", "english": "Remember the word unto thy servant, upon which thou hast caused me to hope.", "transliteration": "z'chor-davar l'avdecha al asher yichaltani"},
    {"verse": 50, "letter": 7, "section": 2, "hebrew": "זֹאת נֶחָמָתִי בְעָנְיִי כִּי אִמְרָתְךָ חִיָּתְנִי", "english": "This is my comfort in my affliction: for thy word hath quickened me.", "transliteration": "zot nechamati v'onyi ki imrat'cha chiyat'ni"},
    {"verse": 51, "letter": 7, "section": 3, "hebrew": "זֵדִים הֱלִיצֻנִי עַד־מְאֹד מִתּוֹרָתְךָ לֹא נָטִיתִי", "english": "The proud have had me greatly in derision: yet have I not declined from thy law.", "transliteration": "zeidim helitzuni ad-m'od mitorat'cha lo natiti"},
    {"verse": 52, "letter": 7, "section": 4, "hebrew": "זָכַרְתִּי מִשְׁפָּטֶיךָ מֵעוֹלָם יְהוָה וָאֶתְנֶחָם", "english": "I remembered thy judgments of old, O LORD; and have comforted myself.", "transliteration": "zacharti mishpateicha me'olam adonai va'etnecham"},
    {"verse": 53, "letter": 7, "section": 5, "hebrew": "זַלְעָפָה אֲחָזַתְנִי מֵרְשָׁעִים עֹזְבֵי תוֹרָתֶךָ", "english": "Horror hath taken hold upon me because of the wicked that forsake thy law.", "transliteration": "zal'afah achazat'ni mer'sha'im oz'vei toratecha"},
    {"verse": 54, "letter": 7, "section": 6, "hebrew": "זְמִרוֹת הָיוּ־לִי חֻקֶּיךָ בְּבֵית מְגוּרָי", "english": "Thy statutes have been my songs in the house of my pilgrimage.", "transliteration": "z'mirot hayu-li chukeicha b'veit m'gurai"},
    {"verse": 55, "letter": 7, "section": 7, "hebrew": "זָכַרְתִּי בַלַּיְלָה שִׁמְךָ יְהוָה וָאֶשְׁמְרָה תוֹרָתֶךָ", "english": "I have remembered thy name, O LORD, in the night, and have kept thy law.", "transliteration": "zacharti valaylah shim'cha adonai va'eshm'rah toratecha"},
    {"verse": 56, "letter": 7, "section": 8, "hebrew": "זֹאת הָיְתָה־לִּי כִּי פִקֻּדֶיךָ נָצָרְתִּי", "english": "This I had, because I kept thy precepts.", "transliteration": "zot hay'tah-li ki fikudeicha natzarti"},

    # ח (Het) - verses 57-64
    {"verse": 57, "letter": 8, "section": 1, "hebrew": "חֶלְקִי יְהוָה אָמַרְתִּי לִשְׁמֹר דְּבָרֶיךָ", "english": "Thou art my portion, O LORD: I have said that I would keep thy words.", "transliteration": "chelki adonai amarti lishmor d'vareicha"},
    {"verse": 58, "letter": 8, "section": 2, "hebrew": "חִלִּיתִי פָנֶיךָ בְכָל־לֵב חָנֵּנִי כְּאִמְרָתֶךָ", "english": "I intreated thy favour with my whole heart: be merciful unto me according to thy word.", "transliteration": "chiliti faneicha v'chol-lev chaneini k'imratecha"},
    {"verse": 59, "letter": 8, "section": 3, "hebrew": "חִשַּׁבְתִּי דְרָכָי וָאָשִׁיבָה רַגְלַי אֶל־עֵדֹתֶיךָ", "english": "I thought on my ways, and turned my feet unto thy testimonies.", "transliteration": "chishavti d'rachai va'ashivah raglai el-edoteicha"},
    {"verse": 60, "letter": 8, "section": 4, "hebrew": "חַשְׁתִּי וְלֹא הִתְמַהְמָהְתִּי לִשְׁמֹר מִצְוֹתֶיךָ", "english": "I made haste, and delayed not to keep thy commandments.", "transliteration": "chashti v'lo hitmahmahti lishmor mitzvoteicha"},
    {"verse": 61, "letter": 8, "section": 5, "hebrew": "חֶבְלֵי רְשָׁעִים עִוְּדֻנִי תּוֹרָתְךָ לֹא שָׁכָחְתִּי", "english": "The bands of the wicked have robbed me: but I have not forgotten thy law.", "transliteration": "chevlei r'sha'im iv'duni torat'cha lo shachachti"},
    {"verse": 62, "letter": 8, "section": 6, "hebrew": "חֲצוֹת־לַיְלָה אָקוּם לְהוֹדוֹת לָךְ עַל מִשְׁפְּטֵי צִדְקֶךָ", "english": "At midnight I will rise to give thanks unto thee because of thy righteous judgments.", "transliteration": "chatzot-laylah akum l'hodot lach al mishp'tei tzidkecha"},
    {"verse": 63, "letter": 8, "section": 7, "hebrew": "חָבֵר אָנִי לְכָל־אֲשֶׁר יְרֵאוּךָ וּלְשֹׁמְרֵי פִּקּוּדֶיךָ", "english": "I am a companion of all them that fear thee, and of them that keep thy precepts.", "transliteration": "chaver ani l'chol-asher y're'ucha ul'shom'rei pikudeicha"},
    {"verse": 64, "letter": 8, "section": 8, "hebrew": "חַסְדְּךָ יְהוָה מָלְאָה הָאָרֶץ חֻקֶּיךָ לַמְּדֵנִי", "english": "The earth, O LORD, is full of thy mercy: teach me thy statutes.", "transliteration": "chasd'cha adonai mal'ah ha'aretz chukeicha lam'deini"},

    # ט (Tet) - verses 65-72
    {"verse": 65, "letter": 9, "section": 1, "hebrew": "טוֹב עָשִׂיתָ עִם־עַבְדְּךָ יְהוָה כִּדְבָרֶךָ", "english": "Thou hast dealt well with thy servant, O LORD, according unto thy word.", "transliteration": "tov asita im-avd'cha adonai kid'varecha"},
    {"verse": 66, "letter": 9, "section": 2, "hebrew": "טוּב טַעַם וָדַעַת לַמְּדֵנִי כִּי בְמִצְוֹתֶיךָ הֶאֱמָנְתִּי", "english": "Teach me good judgment and knowledge: for I have believed thy commandments.", "transliteration": "tuv ta'am vada'at lam'deini ki v'mitzvoteicha he'emanti"},
    {"verse": 67, "letter": 9, "section": 3, "hebrew": "טֶרֶם אֶעֱנֶה אֲנִי שֹׁגֵג וְעַתָּה אִמְרָתְךָ שָׁמָרְתִּי", "english": "Before I was afflicted I went astray: but now have I kept thy word.", "transliteration": "terem e'eneh ani shogeg v'atah imrat'cha shamarti"},
    {"verse": 68, "letter": 9, "section": 4, "hebrew": "טוֹב־אַתָּה וּמֵטִיב לַמְּדֵנִי חֻקֶּיךָ", "english": "Thou art good, and doest good; teach me thy statutes.", "transliteration": "tov-atah um'etiv lam'deini chukeicha"},
    {"verse": 69, "letter": 9, "section": 5, "hebrew": "טָפְלוּ עָלַי שֶׁקֶר זֵדִים אֲנִי בְּכָל־לֵב אֶצֹּר פִּקּוּדֶיךָ", "english": "The proud have forged a lie against me: but I will keep thy precepts with my whole heart.", "transliteration": "taf'lu alai sheker zeidim ani b'chol-lev etsor pikudeicha"},
    {"verse": 70, "letter": 9, "section": 6, "hebrew": "טָפַשׁ כַּחֵלֶב לִבָּם אֲנִי תוֹרָתְךָ שִׁעֲשָׁעְתִּי", "english": "Their heart is as fat as grease; but I delight in thy law.", "transliteration": "tafash kachelev libam ani torat'cha shi'asha'ti"},
    {"verse": 71, "letter": 9, "section": 7, "hebrew": "טוֹב־לִי כִי־עֻנֵּיתִי לְמַעַן אֶלְמַד חֻקֶּיךָ", "english": "It is good for me that I have been afflicted; that I might learn thy statutes.", "transliteration": "tov-li ki-uneiti l'ma'an elmad chukeicha"},
    {"verse": 72, "letter": 9, "section": 8, "hebrew": "טוֹב־לִי תוֹרַת־פִּיךָ מֵאַלְפֵי זָהָב וָכָסֶף", "english": "The law of thy mouth is better unto me than thousands of gold and silver.", "transliteration": "tov-li torat-picha me'alfei zahav vachase'f"},

    # י (Yod) - verses 73-80
    {"verse": 73, "letter": 10, "section": 1, "hebrew": "יָדֶיךָ עָשׂוּנִי וַיְכוֹנְנוּנִי הֲבִינֵנִי וְאֶלְמְדָה מִצְוֹתֶיךָ", "english": "Thy hands have made me and fashioned me: give me understanding, that I may learn thy commandments.", "transliteration": "yadeicha asuni vay'chon'nuni havineini v'elm'dah mitzvoteicha"},
    {"verse": 74, "letter": 10, "section": 2, "hebrew": "יְרֵאֶיךָ יִרְאוּנִי וְיִשְׂמָחוּ כִּי לִדְבָרְךָ יִחָלְתִּי", "english": "They that fear thee will be glad when they see me; because I have hoped in thy word.", "transliteration": "y're'eicha yir'uni v'yism'chu ki lid'var'cha yichalti"},
    {"verse": 75, "letter": 10, "section": 3, "hebrew": "יָדַעְתִּי יְהוָה כִּי־צֶדֶק מִשְׁפָּטֶיךָ וֶאֱמוּנָה עִנִּיתָנִי", "english": "I know, O LORD, that thy judgments are right, and that thou in faithfulness hast afflicted me.", "transliteration": "yada'ti adonai ki-tzedek mishpateicha ve'emunah initani"},
    {"verse": 76, "letter": 10, "section": 4, "hebrew": "יְהִי־נָא חַסְדְּךָ לְנַחֲמֵנִי כְּאִמְרָתְךָ לְעַבְדֶּךָ", "english": "Let, I pray thee, thy merciful kindness be for my comfort, according to thy word unto thy servant.", "transliteration": "y'hi-na chasd'cha l'nachameini k'imrat'cha l'avdecha"},
    {"verse": 77, "letter": 10, "section": 5, "hebrew": "יְבֹאוּנִי רַחֲמֶיךָ וְאֶחְיֶה כִּי־תוֹרָתְךָ שַׁעֲשֻׁעָי", "english": "Let thy tender mercies come unto me, that I may live: for thy law is my delight.", "transliteration": "y'vo'uni rachameicha v'echyeh ki-torat'cha sha'ashu'ai"},
    {"verse": 78, "letter": 10, "section": 6, "hebrew": "יֵבֹשׁוּ זֵדִים כִּי־שֶׁקֶר עִוְּתוּנִי אֲנִי אָשִׂיחַ בְּפִקֻּדֶיךָ", "english": "Let the proud be ashamed; for they dealt perversely with me without a cause: but I will meditate in thy precepts.", "transliteration": "yevoshu zeidim ki-sheker iv'tuni ani asiach b'fikudeicha"},
    {"verse": 79, "letter": 10, "section": 7, "hebrew": "יָשׁוּבוּ לִי יְרֵאֶיךָ וְיֹדְעֵי עֵדֹתֶיךָ", "english": "Let those that fear thee turn unto me, and those that have known thy testimonies.", "transliteration": "yashuvu li y're'eicha v'yod'ei edoteicha"},
    {"verse": 80, "letter": 10, "section": 8, "hebrew": "יְהִי־לִבִּי תָמִים בְּחֻקֶּיךָ לְמַעַן לֹא אֵבוֹשׁ", "english": "Let my heart be sound in thy statutes; that I be not ashamed.", "transliteration": "y'hi-libi tamim b'chukeicha l'ma'an lo evosh"},

    # כ (Kaf) - verses 81-88
    {"verse": 81, "letter": 11, "section": 1, "hebrew": "כָּלְתָה לִתְשׁוּעָתְךָ נַפְשִׁי לִדְבָרְךָ יִחָלְתִּי", "english": "My soul fainteth for thy salvation: but I hope in thy word.", "transliteration": "kal'tah lit'shu'at'cha nafshi lid'var'cha yichalti"},
    {"verse": 82, "letter": 11, "section": 2, "hebrew": "כָּלוּ עֵינַי לְאִמְרָתֶךָ לֵאמֹר מָתַי תְּנַחֲמֵנִי", "english": "Mine eyes fail for thy word, saying, When wilt thou comfort me?", "transliteration": "kalu einai l'imratecha lemor matai t'nachameini"},
    {"verse": 83, "letter": 11, "section": 3, "hebrew": "כִּי־הָיִיתִי כְּנֹאד בְּקִיטוֹר חֻקֶּיךָ לֹא שָׁכָחְתִּי", "english": "For I am become like a bottle in the smoke; yet do I not forget thy statutes.", "transliteration": "ki-hayiti k'no'ad b'kitor chukeicha lo shachachti"},
    {"verse": 84, "letter": 11, "section": 4, "hebrew": "כַּמָּה יְמֵי־עַבְדֶּךָ מָתַי תַּעֲשֶׂה בְרֹדְפַי מִשְׁפָּט", "english": "How many are the days of thy servant? when wilt thou execute judgment on them that persecute me?", "transliteration": "kamah y'mei-avdecha matai ta'aseh v'rod'fai mishpat"},
    {"verse": 85, "letter": 11, "section": 5, "hebrew": "כָּרוּ־לִי זֵדִים שִׁיחוֹת אֲשֶׁר לֹא כְתוֹרָתֶךָ", "english": "The proud have digged pits for me, which are not after thy law.", "transliteration": "karu-li zeidim shichot asher lo ch'toratecha"},
    {"verse": 86, "letter": 11, "section": 6, "hebrew": "כָּל־מִצְוֹתֶיךָ אֱמוּנָה שֶׁקֶר רְדָפוּנִי עָזְרֵנִי", "english": "All thy commandments are faithful: they persecute me wrongfully; help thou me.", "transliteration": "kol-mitzvoteicha emunah sheker r'dafuni oz'reini"},
    {"verse": 87, "letter": 11, "section": 7, "hebrew": "כִּמְעַט כִּלּוּנִי בָאָרֶץ וַאֲנִי לֹא־עָזַבְתִּי פִקֻּדֶיךָ", "english": "They had almost consumed me upon earth; but I forsook not thy precepts.", "transliteration": "kim'at kiluni va'aretz va'ani lo-azavti fikudeicha"},
    {"verse": 88, "letter": 11, "section": 8, "hebrew": "כְּחַסְדְּךָ חַיֵּנִי וְאֶשְׁמְרָה עֵדוּת פִּיךָ", "english": "Quicken me after thy lovingkindness; so shall I keep the testimony of thy mouth.", "transliteration": "k'chasd'cha chayeini v'eshm'rah edut picha"},

    # ל (Lamed) - verses 89-96
    {"verse": 89, "letter": 12, "section": 1, "hebrew": "לְעוֹלָם יְהוָה דְּבָרְךָ נִצָּב בַּשָּׁמָיִם", "english": "For ever, O LORD, thy word is settled in heaven.", "transliteration": "l'olam adonai d'var'cha nitzav bashamayim"},
    {"verse": 90, "letter": 12, "section": 2, "hebrew": "לְדֹר וָדֹר אֱמוּנָתֶךָ כּוֹנַנְתָּ אֶרֶץ וַתַּעֲמֹד", "english": "Thy faithfulness is unto all generations: thou hast established the earth, and it abideth.", "transliteration": "l'dor vador emunateche konanta eretz vata'amod"},
    {"verse": 91, "letter": 12, "section": 3, "hebrew": "לְמִשְׁפָּטֶיךָ עָמְדוּ הַיּוֹם כִּי הַכֹּל עֲבָדֶיךָ", "english": "They continue this day according to thine ordinances: for all are thy servants.", "transliteration": "l'mishpateicha am'du hayom ki hakol avadeicha"},
    {"verse": 92, "letter": 12, "section": 4, "hebrew": "לוּלֵי תוֹרָתְךָ שַׁעֲשֻׁעָי אָז אָבַדְתִּי בְעָנְיִי", "english": "Unless thy law had been my delights, I should then have perished in mine affliction.", "transliteration": "lulei torat'cha sha'ashu'ai az avadti v'onyi"},
    {"verse": 93, "letter": 12, "section": 5, "hebrew": "לְעוֹלָם לֹא־אֶשְׁכַּח פִּקֻּדֶיךָ כִּי בָם חִיִּיתָנִי", "english": "I will never forget thy precepts: for with them thou hast quickened me.", "transliteration": "l'olam lo-eshkach pikudeicha ki vam chiyitani"},
    {"verse": 94, "letter": 12, "section": 6, "hebrew": "לְךָ־אֲנִי הוֹשִׁיעֵנִי כִּי פִקֻּדֶיךָ דָרָשְׁתִּי", "english": "I am thine, save me; for I have sought thy precepts.", "transliteration": "l'cha-ani hoshieini ki fikudeicha darashti"},
    {"verse": 95, "letter": 12, "section": 7, "hebrew": "לִי קִוּוּ רְשָׁעִים לְאַבְּדֵנִי עֵדֹתֶיךָ אֶתְבּוֹנָן", "english": "The wicked have waited for me to destroy me: but I will consider thy testimonies.", "transliteration": "li kivu r'sha'im l'ab'deini edoteicha etbonan"},
    {"verse": 96, "letter": 12, "section": 8, "hebrew": "לְכָל־תִּכְלָה רָאִיתִי קֵץ רְחָבָה מִצְוָתְךָ מְאֹד", "english": "I have seen an end of all perfection: but thy commandment is exceeding broad.", "transliteration": "l'chol-tichlah raiti ketz r'chavah mitzvat'cha m'od"},

    # מ (Mem) - verses 97-104
    {"verse": 97, "letter": 13, "section": 1, "hebrew": "מָה־אָהַבְתִּי תוֹרָתֶךָ כָּל־הַיּוֹם הִיא שִׂיחָתִי", "english": "O how love I thy law! it is my meditation all the day.", "transliteration": "mah-ahavti toratecha kol-hayom hi sichati"},
    {"verse": 98, "letter": 13, "section": 2, "hebrew": "מֵאֹיְבַי תְּחַכְּמֵנִי מִצְוָתֶךָ כִּי לְעוֹלָם הִיא־לִי", "english": "Thou through thy commandments hast made me wiser than mine enemies: for they are ever with me.", "transliteration": "me'oy'vai t'chak'meini mitzvat'cha ki l'olam hi-li"},
    {"verse": 99, "letter": 13, "section": 3, "hebrew": "מִכָּל־מְלַמְּדַי הִשְׂכַּלְתִּי כִּי עֵדְוֹתֶיךָ שִׂיחָה לִּי", "english": "I have more understanding than all my teachers: for thy testimonies are my meditation.", "transliteration": "mikol-m'lam'dai his'kalti ki edvoteicha sichah li"},
    {"verse": 100, "letter": 13, "section": 4, "hebrew": "מִזְּקֵנִים אֶתְבּוֹנָן כִּי פִקֻּדֶיךָ נָצָרְתִּי", "english": "I understand more than the ancients, because I keep thy precepts.", "transliteration": "miz'keinim etbonan ki fikudeicha natzarti"},
    {"verse": 101, "letter": 13, "section": 5, "hebrew": "מִכָּל־אֹרַח רָע כָּלִאתִי רַגְלָי לְמַעַן אֶשְׁמֹר דְּבָרֶךָ", "english": "I have refrained my feet from every evil way, that I might keep thy word.", "transliteration": "mikol-orach ra kaliti raglai l'ma'an eshmor d'varecha"},
    {"verse": 102, "letter": 13, "section": 6, "hebrew": "מִמִּשְׁפָּטֶיךָ לֹא־סָרְתִּי כִּי־אַתָּה הוֹרֵתָנִי", "english": "I have not departed from thy judgments: for thou hast taught me.", "transliteration": "mimishpateicha lo-sarti ki-atah horetani"},
    {"verse": 103, "letter": 13, "section": 7, "hebrew": "מַה־נִּמְלְצוּ לְחִכִּי אִמְרָתֶךָ מִדְּבַשׁ לְפִי", "english": "How sweet are thy words unto my taste! yea, sweeter than honey to my mouth!", "transliteration": "mah-niml'tzu l'chiki imratecha mid'vash l'fi"},
    {"verse": 104, "letter": 13, "section": 8, "hebrew": "מִפִּקּוּדֶיךָ אֶתְבּוֹנָן עַל־כֵּן שָׂנֵאתִי כָּל־אֹרַח שָׁקֶר", "english": "Through thy precepts I get understanding: therefore I hate every false way.", "transliteration": "mipikudeicha etbonan al-ken saneiti kol-orach shaker"},

    # נ (Nun) - verses 105-112
    {"verse": 105, "letter": 14, "section": 1, "hebrew": "נֵר לְרַגְלִי דְבָרֶךָ וְאוֹר לִנְתִיבָתִי", "english": "Thy word is a lamp unto my feet, and a light unto my path.", "transliteration": "ner l'ragli d'varecha v'or lin'tivati"},
    {"verse": 106, "letter": 14, "section": 2, "hebrew": "נִשְׁבַּעְתִּי וָאֲקַיֵּמָה לִשְׁמֹר מִשְׁפְּטֵי צִדְקֶךָ", "english": "I have sworn, and I will perform it, that I will keep thy righteous judgments.", "transliteration": "nishba'ti va'akayemah lishmor mishp'tei tzidkecha"},
    {"verse": 107, "letter": 14, "section": 3, "hebrew": "נַעֲנֵיתִי עַד־מְאֹד יְהוָה חַיֵּנִי כִדְבָרֶךָ", "english": "I am afflicted very much: quicken me, O LORD, according unto thy word.", "transliteration": "na'aneiti ad-m'od adonai chayeini chid'varecha"},
    {"verse": 108, "letter": 14, "section": 4, "hebrew": "נִדְבוֹת פִּי רְצֵה־נָא יְהוָה וּמִשְׁפָּטֶיךָ לַמְּדֵנִי", "english": "Accept, I beseech thee, the freewill offerings of my mouth, O LORD, and teach me thy judgments.", "transliteration": "nid'vot pi r'tzeh-na adonai umishpateicha lam'deini"},
    {"verse": 109, "letter": 14, "section": 5, "hebrew": "נַפְשִׁי בְכַפִּי תָמִיד וְתוֹרָתְךָ לֹא שָׁכָחְתִּי", "english": "My soul is continually in my hand: yet do I not forget thy law.", "transliteration": "nafshi v'chapi tamid v'torat'cha lo shachachti"},
    {"verse": 110, "letter": 14, "section": 6, "hebrew": "נָתְנוּ רְשָׁעִים פַּח לִי וּמִפִּקּוּדֶיךָ לֹא תָעִיתִי", "english": "The wicked have laid a snare for me: yet I erred not from thy precepts.", "transliteration": "nat'nu r'sha'im pach li umipikudeicha lo ta'iti"},
    {"verse": 111, "letter": 14, "section": 7, "hebrew": "נָחַלְתִּי עֵדְוֹתֶיךָ לְעוֹלָם כִּי־שְׂשׂוֹן לִבִּי הֵמָּה", "english": "Thy testimonies have I taken as an heritage for ever: for they are the rejoicing of my heart.", "transliteration": "nachalti edvoteicha l'olam ki-s'son libi hemah"},
    {"verse": 112, "letter": 14, "section": 8, "hebrew": "נָטִיתִי לִבִּי לַעֲשׂוֹת חֻקֶּיךָ לְעוֹלָם עֵקֶב", "english": "I have inclined mine heart to perform thy statutes alway, even unto the end.", "transliteration": "natiti libi la'asot chukeicha l'olam ekev"},

    # ס (Samech) - verses 113-120
    {"verse": 113, "letter": 15, "section": 1, "hebrew": "סֵעֲפִים שָׂנֵאתִי וְתוֹרָתְךָ אָהָבְתִּי", "english": "I hate vain thoughts: but thy law do I love.", "transliteration": "se'afim saneiti v'torat'cha ahavti"},
    {"verse": 114, "letter": 15, "section": 2, "hebrew": "סִתְרִי וּמָגִנִּי אָתָּה לִדְבָרְךָ יִחָלְתִּי", "english": "Thou art my hiding place and my shield: I hope in thy word.", "transliteration": "sitri umagini atah lid'var'cha yichalti"},
    {"verse": 115, "letter": 15, "section": 3, "hebrew": "סוּרוּ־מִמֶּנִּי מְרֵעִים וְאֶצְּרָה מִצְוֹת אֱלֹהָי", "english": "Depart from me, ye evildoers: for I will keep the commandments of my God.", "transliteration": "suru-mimenni m'reim v'etz'rah mitzvot elohai"},
    {"verse": 116, "letter": 15, "section": 4, "hebrew": "סָמְכֵנִי כְאִמְרָתְךָ וְאֶחְיֶה וְאַל־תְּבִישֵׁנִי מִשִּׂבְרִי", "english": "Uphold me according unto thy word, that I may live: and let me not be ashamed of my hope.", "transliteration": "sam'cheini ch'imrat'cha v'echyeh v'al-t'visheini misivri"},
    {"verse": 117, "letter": 15, "section": 5, "hebrew": "סְעָדֵנִי וְאִוָּשֵׁעָה וְאֶשְׁעָה בְחֻקֶּיךָ תָמִיד", "english": "Hold thou me up, and I shall be safe: and I will have respect unto thy statutes continually.", "transliteration": "s'adeini v'ivashea'ah v'esh'ah v'chukeicha tamid"},
    {"verse": 118, "letter": 15, "section": 6, "hebrew": "סָלִיתָ כָּל־שֹׁגִים מֵחֻקֶּיךָ כִּי־שֶׁקֶר תַּרְמִיתָם", "english": "Thou hast trodden down all them that err from thy statutes: for their deceit is falsehood.", "transliteration": "salita kol-shogim mechukeicha ki-sheker tarmitam"},
    {"verse": 119, "letter": 15, "section": 7, "hebrew": "סִגִים הִשְׁבַּתָּ כָל־רִשְׁעֵי־אָרֶץ לָכֵן אָהַבְתִּי עֵדֹתֶיךָ", "english": "Thou puttest away all the wicked of the earth like dross: therefore I love thy testimonies.", "transliteration": "sigim hishbata kol-rish'ei-aretz lachen ahavti edoteicha"},
    {"verse": 120, "letter": 15, "section": 8, "hebrew": "סָמַר מִפַּחְדְּךָ בְשָׂרִי וּמִמִּשְׁפָּטֶיךָ יָרֵאתִי", "english": "My flesh trembleth for fear of thee; and I am afraid of thy judgments.", "transliteration": "samar mipachd'cha v'sari umimishpateicha yareiti"},

    # ע (Ayin) - verses 121-128
    {"verse": 121, "letter": 16, "section": 1, "hebrew": "עָשִׂיתִי מִשְׁפָּט וָצֶדֶק אַל־תַּנִּיחֵנִי לְעֹשְׁקָי", "english": "I have done judgment and justice: leave me not to mine oppressors.", "transliteration": "asiti mishpat vatzedek al-tanicheni l'osh'kai"},
    {"verse": 122, "letter": 16, "section": 2, "hebrew": "עֲרֹב עַבְדְּךָ לְטוֹב אַל־יַעַשְׁקֻנִי זֵדִים", "english": "Be surety for thy servant for good: let not the proud oppress me.", "transliteration": "arov avd'cha l'tov al-ya'ashkuni zeidim"},
    {"verse": 123, "letter": 16, "section": 3, "hebrew": "עֵינַי כָּלוּ לִישׁוּעָתֶךָ וּלְאִמְרַת צִדְקֶךָ", "english": "Mine eyes fail for thy salvation, and for the word of thy righteousness.", "transliteration": "einai kalu li'shu'atecha ul'imrat tzidkecha"},
    {"verse": 124, "letter": 16, "section": 4, "hebrew": "עֲשֵׂה עִם־עַבְדְּךָ כְחַסְדֶּךָ וְחֻקֶּיךָ לַמְּדֵנִי", "english": "Deal with thy servant according unto thy mercy, and teach me thy statutes.", "transliteration": "aseh im-avd'cha k'chasdecha v'chukeicha lam'deini"},
    {"verse": 125, "letter": 16, "section": 5, "hebrew": "עַבְדְּךָ־אָנִי הֲבִינֵנִי וְאֵדְעָה עֵדֹתֶיךָ", "english": "I am thy servant; give me understanding, that I may know thy testimonies.", "transliteration": "avd'cha-ani havineini v'ed'ah edoteicha"},
    {"verse": 126, "letter": 16, "section": 6, "hebrew": "עֵת לַעֲשׂוֹת לַיהוָה הֵפֵרוּ תּוֹרָתֶךָ", "english": "It is time for thee, LORD, to work: for they have made void thy law.", "transliteration": "et la'asot ladonai heferu toratecha"},
    {"verse": 127, "letter": 16, "section": 7, "hebrew": "עַל־כֵּן אָהַבְתִּי מִצְוֹתֶיךָ מִזָּהָב וּמִפָּז", "english": "Therefore I love thy commandments above gold; yea, above fine gold.", "transliteration": "al-ken ahavti mitzvoteicha mizahav umipaz"},
    {"verse": 128, "letter": 16, "section": 8, "hebrew": "עַל־כֵּן כָּל־פִּקּוּדֵי כֹל יִשָּׁרְתִּי כָּל־אֹרַח שֶׁקֶר שָׂנֵאתִי", "english": "Therefore I esteem all thy precepts concerning all things to be right; and I hate every false way.", "transliteration": "al-ken kol-pikudei chol yisharti kol-orach sheker saneiti"},

    # פ (Pe) - verses 129-136
    {"verse": 129, "letter": 17, "section": 1, "hebrew": "פְּלָאוֹת עֵדְוֹתֶיךָ עַל־כֵּן נְצָרַתְם נַפְשִׁי", "english": "Thy testimonies are wonderful: therefore doth my soul keep them.", "transliteration": "p'laot edvoteicha al-ken n'tzaratam nafshi"},
    {"verse": 130, "letter": 17, "section": 2, "hebrew": "פֵּתַח דְּבָרֶיךָ יָאִיר מֵבִין פְּתָיִים", "english": "The entrance of thy words giveth light; it giveth understanding unto the simple.", "transliteration": "petach d'vareicha yair mevin p'tayim"},
    {"verse": 131, "letter": 17, "section": 3, "hebrew": "פִּי־פָעַרְתִּי וָאֶשְׁאָפָה כִּי לְמִצְוֹתֶיךָ יָאָבְתִּי", "english": "I opened my mouth, and panted: for I longed for thy commandments.", "transliteration": "pi-fa'arti va'esh'afah ki l'mitzvoteicha ya'avti"},
    {"verse": 132, "letter": 17, "section": 4, "hebrew": "פְּנֵה־אֵלַי וְחָנֵּנִי כְּמִשְׁפַּט לְאֹהֲבֵי שְׁמֶךָ", "english": "Look thou upon me, and be merciful unto me, as thou usest to do unto those that love thy name.", "transliteration": "p'neh-elai v'chaneini k'mishpat l'ohavei sh'mecha"},
    {"verse": 133, "letter": 17, "section": 5, "hebrew": "פְּעָמַי הָכֵן בְּאִמְרָתֶךָ וְאַל־תַּשְׁלֶט־בִּי כָל־אָוֶן", "english": "Order my steps in thy word: and let not any iniquity have dominion over me.", "transliteration": "p'amai hachen b'imratecha v'al-tashlet-bi chol-aven"},
    {"verse": 134, "letter": 17, "section": 6, "hebrew": "פְּדֵנִי מֵעֹשֶׁק אָדָם וְאֶשְׁמְרָה פִּקּוּדֶיךָ", "english": "Deliver me from the oppression of man: so will I keep thy precepts.", "transliteration": "p'deini me'oshek adam v'eshm'rah pikudeicha"},
    {"verse": 135, "letter": 17, "section": 7, "hebrew": "פָּנֶיךָ הָאֵר בְּעַבְדֶּךָ וְלַמְּדֵנִי אֶת־חֻקֶּיךָ", "english": "Make thy face to shine upon thy servant; and teach me thy statutes.", "transliteration": "paneicha ha'er b'avdecha v'lam'deini et-chukeicha"},
    {"verse": 136, "letter": 17, "section": 8, "hebrew": "פַּלְגֵי־מַיִם יָרְדוּ עֵינָי עַל לֹא־שָׁמְרוּ תוֹרָתֶךָ", "english": "Rivers of waters run down mine eyes, because they keep not thy law.", "transliteration": "palgei-mayim yar'du einai al lo-sham'ru toratecha"},

    # צ (Tzade) - verses 137-144
    {"verse": 137, "letter": 18, "section": 1, "hebrew": "צַדִּיק אַתָּה יְהוָה וְיָשָׁר מִשְׁפָּטֶיךָ", "english": "Righteous art thou, O LORD, and upright are thy judgments.", "transliteration": "tzadik atah adonai v'yashar mishpateicha"},
    {"verse": 138, "letter": 18, "section": 2, "hebrew": "צִוִּיתָ צֶדֶק עֵדֹתֶיךָ וֶאֱמוּנָה מְאֹד", "english": "Thy testimonies that thou hast commanded are righteous and very faithful.", "transliteration": "tzivita tzedek edoteicha ve'emunah m'od"},
    {"verse": 139, "letter": 18, "section": 3, "hebrew": "צִמְּתַתְנִי קִנְאָתִי כִּי־שָׁכְחוּ דְבָרֶיךָ צָרָי", "english": "My zeal hath consumed me, because mine enemies have forgotten thy words.", "transliteration": "tzim'tatni kin'ati ki-shach'chu d'vareicha tzarai"},
    {"verse": 140, "letter": 18, "section": 4, "hebrew": "צְרוּפָה אִמְרָתְךָ מְאֹד וְעַבְדְּךָ אֲהֵבָהּ", "english": "Thy word is very pure: therefore thy servant loveth it.", "transliteration": "tz'rufah imrat'cha m'od v'avd'cha ahevah"},
    {"verse": 141, "letter": 18, "section": 5, "hebrew": "צָעִיר אָנֹכִי וְנִבְזֶה פִּקֻּדֶיךָ לֹא שָׁכָחְתִּי", "english": "I am small and despised: yet do not I forget thy precepts.", "transliteration": "tza'ir anochi v'nivzeh pikudeicha lo shachachti"},
    {"verse": 142, "letter": 18, "section": 6, "hebrew": "צִדְקָתְךָ צֶדֶק לְעוֹלָם וְתוֹרָתְךָ אֱמֶת", "english": "Thy righteousness is an everlasting righteousness, and thy law is the truth.", "transliteration": "tzidkat'cha tzedek l'olam v'torat'cha emet"},
    {"verse": 143, "letter": 18, "section": 7, "hebrew": "צַר־וּמְצוּקָה מְצָאוּנִי מִצְוֹתֶיךָ שַׁעֲשֻׁעָי", "english": "Trouble and anguish have taken hold on me: yet thy commandments are my delights.", "transliteration": "tzar-umtzukah m'tza'uni mitzvoteicha sha'ashu'ai"},
    {"verse": 144, "letter": 18, "section": 8, "hebrew": "צֶדֶק עֵדְוֹתֶיךָ לְעוֹלָם הֲבִינֵנִי וְאֶחְיֶה", "english": "The righteousness of thy testimonies is everlasting: give me understanding, and I shall live.", "transliteration": "tzedek edvoteicha l'olam havineini v'echyeh"},

    # ק (Qof) - verses 145-152
    {"verse": 145, "letter": 19, "section": 1, "hebrew": "קָרָאתִי בְכָל־לֵב עֲנֵנִי יְהוָה חֻקֶּיךָ אֶצֹּרָה", "english": "I cried with my whole heart; hear me, O LORD: I will keep thy statutes.", "transliteration": "karati v'chol-lev aneini adonai chukeicha etzorah"},
    {"verse": 146, "letter": 19, "section": 2, "hebrew": "קְרָאתִיךָ הוֹשִׁיעֵנִי וְאֶשְׁמְרָה עֵדֹתֶיךָ", "english": "I cried unto thee; save me, and I shall keep thy testimonies.", "transliteration": "k'raticha hoshieini v'eshm'rah edoteicha"},
    {"verse": 147, "letter": 19, "section": 3, "hebrew": "קִדַּמְתִּי בַנֶּשֶׁף וָאֲשַׁוֵּעָה לִדְבָרְךָ יִחָלְתִּי", "english": "I prevented the dawning of the morning, and cried: I hoped in thy word.", "transliteration": "kidamti vaneshef va'ashave'ah lid'var'cha yichalti"},
    {"verse": 148, "letter": 19, "section": 4, "hebrew": "קִדְּמוּ עֵינַי אַשְׁמֻרוֹת לָשִׂיחַ בְּאִמְרָתֶךָ", "english": "Mine eyes prevent the night watches, that I might meditate in thy word.", "transliteration": "kid'mu einai ashmurot lasiach b'imratecha"},
    {"verse": 149, "letter": 19, "section": 5, "hebrew": "קוֹלִי שִׁמְעָה כְחַסְדֶּךָ יְהוָה כְּמִשְׁפָּטֶךָ חַיֵּנִי", "english": "Hear my voice according unto thy lovingkindness: O LORD, quicken me according to thy judgment.", "transliteration": "koli shim'ah k'chasdecha adonai k'mishpatecha chayeini"},
    {"verse": 150, "letter": 19, "section": 6, "hebrew": "קָרְבוּ רֹדְפֵי זִמָּה מִתּוֹרָתְךָ רָחָקוּ", "english": "They draw nigh that follow after mischief: they are far from thy law.", "transliteration": "kar'vu rod'fei zimah mitorat'cha rachaku"},
    {"verse": 151, "letter": 19, "section": 7, "hebrew": "קָרוֹב אַתָּה יְהוָה וְכָל־מִצְוֹתֶיךָ אֱמֶת", "english": "Thou art near, O LORD; and all thy commandments are truth.", "transliteration": "karov atah adonai v'chol-mitzvoteicha emet"},
    {"verse": 152, "letter": 19, "section": 8, "hebrew": "קֶדֶם יָדַעְתִּי מֵעֵדֹתֶיךָ כִּי לְעוֹלָם יְסַדְתָּם", "english": "Concerning thy testimonies, I have known of old that thou hast founded them for ever.", "transliteration": "kedem yada'ti me'edoteicha ki l'olam y'sadtam"},

    # ר (Resh) - verses 153-160
    {"verse": 153, "letter": 20, "section": 1, "hebrew": "רְאֵה־עָנְיִי וְחַלְּצֵנִי כִּי־תוֹרָתְךָ לֹא שָׁכָחְתִּי", "english": "Consider mine affliction, and deliver me: for I do not forget thy law.", "transliteration": "r'eh-onyi v'chaltz'ni ki-torat'cha lo shachachti"},
    {"verse": 154, "letter": 20, "section": 2, "hebrew": "רִיבָה רִיבִי וּגְאָלֵנִי לְאִמְרָתְךָ חַיֵּנִי", "english": "Plead my cause, and deliver me: quicken me according to thy word.", "transliteration": "rivah rivi ug'aleini l'imrat'cha chayeini"},
    {"verse": 155, "letter": 20, "section": 3, "hebrew": "רָחוֹק מֵרְשָׁעִים יְשׁוּעָה כִּי חֻקֶּיךָ לֹא דָרָשׁוּ", "english": "Salvation is far from the wicked: for they seek not thy statutes.", "transliteration": "rachok mer'sha'im y'shu'ah ki chukeicha lo darashu"},
    {"verse": 156, "letter": 20, "section": 4, "hebrew": "רַחֲמֶיךָ רַבִּים יְהוָה כְּמִשְׁפָּטֶיךָ חַיֵּנִי", "english": "Great are thy tender mercies, O LORD: quicken me according to thy judgments.", "transliteration": "rachameicha rabim adonai k'mishpateicha chayeini"},
    {"verse": 157, "letter": 20, "section": 5, "hebrew": "רַבִּים רֹדְפַי וְצָרָי מֵעֵדְוֹתֶיךָ לֹא נָטִיתִי", "english": "Many are my persecutors and mine enemies; yet do I not decline from thy testimonies.", "transliteration": "rabim rod'fai v'tzarai me'edvoteicha lo natiti"},
    {"verse": 158, "letter": 20, "section": 6, "hebrew": "רָאִיתִי בֹגְדִים וָאֶתְקוֹטָטָה אֲשֶׁר אִמְרָתְךָ לֹא שָׁמָרוּ", "english": "I beheld the transgressors, and was grieved; because they kept not thy word.", "transliteration": "raiti vog'dim va'etkotehtah asher imrat'cha lo shamaru"},
    {"verse": 159, "letter": 20, "section": 7, "hebrew": "רְאֵה כִּי־פִקֻּדֶיךָ אָהָבְתִּי יְהוָה כְּחַסְדְּךָ חַיֵּנִי", "english": "Consider how I love thy precepts: quicken me, O LORD, according to thy lovingkindness.", "transliteration": "r'eh ki-fikudeicha ahavti adonai k'chasd'cha chayeini"},
    {"verse": 160, "letter": 20, "section": 8, "hebrew": "רֹאשׁ־דְּבָרְךָ אֱמֶת וּלְעוֹלָם כָּל־מִשְׁפַּט צִדְקֶךָ", "english": "Thy word is true from the beginning: and every one of thy righteous judgments endureth for ever.", "transliteration": "rosh-d'var'cha emet ul'olam kol-mishpat tzidkecha"},

    # ש (Shin) - verses 161-168
    {"verse": 161, "letter": 21, "section": 1, "hebrew": "שָׂרִים רְדָפוּנִי חִנָּם וּמִדְּבָרְךָ פָּחַד לִבִּי", "english": "Princes have persecuted me without a cause: but my heart standeth in awe of thy word.", "transliteration": "sarim r'dafuni chinam umid'var'cha pachad libi"},
    {"verse": 162, "letter": 21, "section": 2, "hebrew": "שָׂשׂ אָנֹכִי עַל־אִמְרָתְךָ כְּמוֹצֵא שָׁלָל רָב", "english": "I rejoice at thy word, as one that findeth great spoil.", "transliteration": "sas anochi al-imrat'cha k'motzei shalal rav"},
    {"verse": 163, "letter": 21, "section": 3, "hebrew": "שֶׁקֶר שָׂנֵאתִי וַאֲתַעֵבָה תּוֹרָתְךָ אָהָבְתִּי", "english": "I hate and abhor lying: but thy law do I love.", "transliteration": "sheker saneiti va'ata'evah torat'cha ahavti"},
    {"verse": 164, "letter": 21, "section": 4, "hebrew": "שֶׁבַע בַּיּוֹם הִלַּלְתִּיךָ עַל מִשְׁפְּטֵי צִדְקֶךָ", "english": "Seven times a day do I praise thee because of thy righteous judgments.", "transliteration": "sheva bayom hilalticha al mishp'tei tzidkecha"},
    {"verse": 165, "letter": 21, "section": 5, "hebrew": "שָׁלוֹם רָב לְאֹהֲבֵי תוֹרָתֶךָ וְאֵין־לָמוֹ מִכְשׁוֹל", "english": "Great peace have they which love thy law: and nothing shall offend them.", "transliteration": "shalom rav l'ohavei toratecha v'ein-lamo michshol"},
    {"verse": 166, "letter": 21, "section": 6, "hebrew": "שִׂבַּרְתִּי לִישׁוּעָתְךָ יְהוָה וּמִצְוֹתֶיךָ עָשִׂיתִי", "english": "LORD, I have hoped for thy salvation, and done thy commandments.", "transliteration": "sibarti li'shu'at'cha adonai umitzvoteicha asiti"},
    {"verse": 167, "letter": 21, "section": 7, "hebrew": "שָׁמְרָה נַפְשִׁי עֵדֹתֶיךָ וָאֹהֲבֵם מְאֹד", "english": "My soul hath kept thy testimonies; and I love them exceedingly.", "transliteration": "sham'rah nafshi edoteicha va'ohavem m'od"},
    {"verse": 168, "letter": 21, "section": 8, "hebrew": "שָׁמַרְתִּי פִקֻּדֶיךָ וְעֵדֹתֶיךָ כִּי כָל־דְּרָכַי נֶגְדֶּךָ", "english": "I have kept thy precepts and thy testimonies: for all my ways are before thee.", "transliteration": "shamarti fikudeicha v'edoteicha ki chol-d'rachai negdecha"},

    # ת (Tav) - verses 169-176
    {"verse": 169, "letter": 22, "section": 1, "hebrew": "תִּקְרַב רִנָּתִי לְפָנֶיךָ יְהוָה כִּדְבָרְךָ הֲבִינֵנִי", "english": "Let my cry come near before thee, O LORD: give me understanding according to thy word.", "transliteration": "tikrav rinati l'faneicha adonai kid'var'cha havineini"},
    {"verse": 170, "letter": 22, "section": 2, "hebrew": "תָּבוֹא תְּחִנָּתִי לְפָנֶיךָ כְּאִמְרָתְךָ הַצִּילֵנִי", "english": "Let my supplication come before thee: deliver me according to thy word.", "transliteration": "tavo t'chinati l'faneicha k'imrat'cha hatzileini"},
    {"verse": 171, "letter": 22, "section": 3, "hebrew": "תַּבַּעְנָה שְׂפָתַי תְּהִלָּה כִּי תְלַמְּדֵנִי חֻקֶּיךָ", "english": "My lips shall utter praise, when thou hast taught me thy statutes.", "transliteration": "taba'nah s'fatai t'hilah ki t'lam'deini chukeicha"},
    {"verse": 172, "letter": 22, "section": 4, "hebrew": "תַּעַן לְשׁוֹנִי אִמְרָתֶךָ כִּי כָל־מִצְוֹתֶיךָ צֶדֶק", "english": "My tongue shall speak of thy word: for all thy commandments are righteousness.", "transliteration": "ta'an l'shoni imratecha ki chol-mitzvoteicha tzedek"},
    {"verse": 173, "letter": 22, "section": 5, "hebrew": "תְּהִי־יָדְךָ לְעָזְרֵנִי כִּי פִקֻּדֶיךָ בָחָרְתִּי", "english": "Let thine hand help me; for I have chosen thy precepts.", "transliteration": "t'hi-yad'cha l'oz'reini ki fikudeicha vacharti"},
    {"verse": 174, "letter": 22, "section": 6, "hebrew": "תָּאַבְתִּי לִישׁוּעָתְךָ יְהוָה וְתוֹרָתְךָ שַׁעֲשֻׁעָי", "english": "I have longed for thy salvation, O LORD; and thy law is my delight.", "transliteration": "ta'avti li'shu'at'cha adonai v'torat'cha sha'ashu'ai"},
    {"verse": 175, "letter": 22, "section": 7, "hebrew": "תְּחִי־נַפְשִׁי וּתְהַלְלֶךָּ וּמִשְׁפָּטֶיךָ יַעְזְרֻנִי", "english": "Let my soul live, and it shall praise thee; and let thy judgments help me.", "transliteration": "t'chi-nafshi ut'halecha umishpateicha ya'z'runi"},
    {"verse": 176, "letter": 22, "section": 8, "hebrew": "תָּעִיתִי כְּשֶׂה אֹבֵד בַּקֵּשׁ עַבְדֶּךָ כִּי מִצְוֹתֶיךָ לֹא שָׁכָחְתִּי", "english": "I have gone astray like a lost sheep; seek thy servant; for I do not forget thy commandments.", "transliteration": "ta'iti k'seh oved bakesh avdecha ki mitzvoteicha lo shachachti"}
]

# All 176 verses are now included in PSALM_119_VERSES above
# This completes the full Psalm 119 implementation

# Additional Hebrew themes and keywords for verses
VERSE_THEMES = {
    "torah": "תורה",
    "commandments": "מצוות", 
    "statutes": "חוקים",
    "testimonies": "עדות",
    "precepts": "פקודים",
    "judgments": "משפטים",
    "word": "דבר",
    "heart": "לב",
    "soul": "נפש",
    "path": "דרך",
    "way": "אורח",
    "blessed": "אשרי",
    "righteousness": "צדק",
    "understanding": "בינה",
    "wisdom": "חכמה",
    "fear": "יראה",
    "love": "אהבה",
    "delight": "שעשועים",
    "meditation": "שיח",
    "trust": "בטחון",
    "salvation": "תשועה"
}

async def create_hebrew_letters(session: AsyncSession) -> Dict[int, Psalm119Letter]:
    """
    Create and populate Hebrew letters for Psalm 119.
    
    Args:
        session: Database session
        
    Returns:
        Dictionary mapping letter IDs to letter objects
    """
    logger.info("Creating Hebrew letters for Psalm 119...")
    
    letters_dict = {}
    
    for letter_data in HEBREW_LETTERS_DATA:
        # Check if letter already exists
        result = await session.execute(
            select(Psalm119Letter).where(Psalm119Letter.id == letter_data["id"])
        )
        existing_letter = result.scalar_one_or_none()
        
        if existing_letter:
            logger.info(f"Hebrew letter {letter_data['hebrew_letter']} already exists, updating...")
            # Update existing letter
            for key, value in letter_data.items():
                if key != "id":
                    setattr(existing_letter, key, value)
            letters_dict[letter_data["id"]] = existing_letter
        else:
            # Create new letter
            new_letter = Psalm119Letter(**letter_data)
            session.add(new_letter)
            letters_dict[letter_data["id"]] = new_letter
            logger.info(f"Created Hebrew letter: {letter_data['hebrew_letter']} ({letter_data['english_name']})")
    
    await session.commit()
    logger.info(f"Successfully processed {len(letters_dict)} Hebrew letters")
    
    return letters_dict

async def create_psalm_verses(session: AsyncSession, letters_dict: Dict[int, Psalm119Letter]) -> List[Psalm119Verse]:
    """
    Create and populate Psalm 119 verses.
    
    Args:
        session: Database session
        letters_dict: Dictionary of Hebrew letters
        
    Returns:
        List of created verse objects
    """
    logger.info("Creating Psalm 119 verses...")
    
    verses_list = []
    
    # Using all 176 verses of Psalm 119
    for verse_data in PSALM_119_VERSES:
        verse_id = verse_data["verse"]
        
        # Check if verse already exists
        result = await session.execute(
            select(Psalm119Verse).where(Psalm119Verse.id == verse_id)
        )
        existing_verse = result.scalar_one_or_none()
        
        if existing_verse:
            logger.info(f"Verse {verse_id} already exists, updating...")
            # Update existing verse
            existing_verse.letter_id = verse_data["letter"]
            existing_verse.verse_in_section = verse_data["section"]
            existing_verse.verse_number = verse_id
            existing_verse.hebrew_text = verse_data["hebrew"]
            existing_verse.english_text = verse_data["english"]
            existing_verse.transliteration = verse_data["transliteration"]
            
            # Generate additional fields
            existing_verse.update_word_counts()
            existing_verse.generate_no_vowels_text()
            
            # Add themes and keywords
            existing_verse.themes = _generate_verse_themes(verse_data)
            existing_verse.keywords = _generate_verse_keywords(verse_data)
            
            verses_list.append(existing_verse)
        else:
            # Create new verse
            new_verse = Psalm119Verse(
                id=verse_id,
                letter_id=verse_data["letter"],
                verse_in_section=verse_data["section"],
                verse_number=verse_id,
                hebrew_text=verse_data["hebrew"],
                english_text=verse_data["english"],
                transliteration=verse_data["transliteration"],
                themes=_generate_verse_themes(verse_data),
                keywords=_generate_verse_keywords(verse_data)
            )
            
            # Generate additional fields
            new_verse.update_word_counts()
            new_verse.generate_no_vowels_text()
            
            session.add(new_verse)
            verses_list.append(new_verse)
            logger.info(f"Created verse {verse_id}: {verse_data['hebrew'][:50]}...")
    
    await session.commit()
    logger.info(f"Successfully processed {len(verses_list)} verses")
    
    return verses_list

def _generate_verse_themes(verse_data: Dict) -> str:
    """Generate themes for a verse based on its content."""
    themes = []
    hebrew_text = verse_data["hebrew"].lower()
    english_text = verse_data["english"].lower()
    
    # Map English keywords to Hebrew themes
    theme_mapping = {
        "torah": "תורה",
        "law": "תורה",
        "commandment": "מצוות",
        "statute": "חוקים",
        "testimony": "עדות",
        "precept": "פקודים",
        "judgment": "משפטים",
        "word": "דבר",
        "heart": "לב",
        "soul": "נפש",
        "blessed": "ברכה",
        "righteous": "צדק",
        "understand": "בינה",
        "wisdom": "חכמה"
    }
    
    for english_keyword, hebrew_theme in theme_mapping.items():
        if english_keyword in english_text:
            themes.append(hebrew_theme)
    
    return ", ".join(themes) if themes else "תהילים קיט"

def _generate_verse_keywords(verse_data: Dict) -> str:
    """Generate keywords for a verse based on its content."""
    keywords = []
    hebrew_text = verse_data["hebrew"]
    
    # Extract key Hebrew words (simplified)
    key_words = ["תורה", "מצוות", "חוקים", "עדות", "פקודים", "משפטים", "דבר", "לב", "נפש", "דרך"]
    
    for word in key_words:
        if word in hebrew_text:
            keywords.append(word)
    
    # Add letter-specific keywords
    letter_id = verse_data["letter"]
    if letter_id <= len(HEBREW_LETTERS_DATA):
        letter_info = HEBREW_LETTERS_DATA[letter_id - 1]
        keywords.append(letter_info["hebrew_letter"])
        keywords.append(letter_info["hebrew_name"])
    
    return ", ".join(keywords) if keywords else f"פסוק {verse_data['verse']}"

async def verify_data_integrity(session: AsyncSession) -> Dict[str, Any]:
    """
    Verify the integrity of the populated Psalm 119 data.
    
    Args:
        session: Database session
        
    Returns:
        Dictionary with verification results
    """
    logger.info("Verifying Psalm 119 data integrity...")
    
    # Count letters
    letter_count_result = await session.execute(select(text("COUNT(*) FROM psalm_119_letters")))
    letter_count = letter_count_result.scalar()
    
    # Count verses
    verse_count_result = await session.execute(select(text("COUNT(*) FROM psalm_119_verses")))
    verse_count = verse_count_result.scalar()
    
    # Check for missing verse numbers
    missing_verses = []
    for i in range(1, 177):  # Check all 176 verses
        result = await session.execute(
            select(Psalm119Verse).where(Psalm119Verse.verse_number == i)
        )
        if not result.scalar_one_or_none():
            missing_verses.append(i)
    
    # Check letter-verse relationships
    orphaned_verses = await session.execute(
        text("""
            SELECT pv.verse_number 
            FROM psalm_119_verses pv 
            LEFT JOIN psalm_119_letters pl ON pv.letter_id = pl.id 
            WHERE pl.id IS NULL
        """)
    )
    orphaned_verse_numbers = [row[0] for row in orphaned_verses.fetchall()]
    
    verification_result = {
        "total_letters": letter_count,
        "total_verses": verse_count,
        "expected_letters": 22,
        "expected_verses_full": 176,  # Complete Psalm 119
        "missing_verses": missing_verses,
        "orphaned_verses": orphaned_verse_numbers,
        "data_complete": letter_count == 22 and verse_count == 176 and not missing_verses and not orphaned_verse_numbers
    }
    
    logger.info(f"Verification results: {verification_result}")
    return verification_result

async def populate_psalm_119() -> Dict[str, Any]:
    """
    Main function to populate Psalm 119 database.
    
    Returns:
        Dictionary with migration results
    """
    logger.info("Starting Psalm 119 database population...")
    
    try:
        async with get_db_session() as session:
            # Create Hebrew letters
            letters_dict = await create_hebrew_letters(session)
            
            # Create Psalm verses
            verses_list = await create_psalm_verses(session, letters_dict)
            
            # Verify data integrity
            verification = await verify_data_integrity(session)
            
            result = {
                "status": "success",
                "letters_created": len(letters_dict),
                "verses_created": len(verses_list),
                "verification": verification,
                "message": "Psalm 119 database population completed successfully"
            }
            
            logger.info(f"Migration completed: {result}")
            return result
            
    except Exception as e:
        error_msg = f"Error populating Psalm 119 database: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "status": "error",
            "message": error_msg,
            "letters_created": 0,
            "verses_created": 0
        }

# Additional utility functions for Hebrew text processing
def normalize_hebrew_text(text: str) -> str:
    """
    Normalize Hebrew text by removing vowels and standardizing characters.
    
    Args:
        text: Hebrew text to normalize
        
    Returns:
        Normalized Hebrew text
    """
    if not text:
        return ""
    
    # Remove Hebrew vowels (nikud)
    import re
    vowel_pattern = r'[\u05B0-\u05BC\u05C1-\u05C2\u05C4-\u05C5\u05C7]'
    normalized = re.sub(vowel_pattern, '', text)
    
    # Normalize final letters
    final_letters = {
        'ך': 'כ',
        'ם': 'מ', 
        'ן': 'נ',
        'ף': 'פ',
        'ץ': 'צ'
    }
    
    for final, regular in final_letters.items():
        normalized = normalized.replace(final, regular)
    
    return normalized

def extract_hebrew_roots(text: str) -> List[str]:
    """
    Extract Hebrew word roots from text (simplified version).
    
    Args:
        text: Hebrew text
        
    Returns:
        List of potential Hebrew roots
    """
    import re
    
    # Remove vowels and punctuation
    clean_text = normalize_hebrew_text(text)
    
    # Split into words
    words = re.findall(r'[\u05D0-\u05EA]+', clean_text)
    
    # Extract potential 3-letter roots (simplified)
    roots = []
    for word in words:
        if len(word) >= 3:
            # Take first 3 letters as potential root (very simplified)
            potential_root = word[:3]
            if potential_root not in roots:
                roots.append(potential_root)
    
    return roots

# CLI interface for running the migration
if __name__ == "__main__":
    import sys
    
    async def main():
        """Main CLI function."""
        print("Psalm 119 Hebrew Memorial Database Migration")
        print("=" * 50)
        
        try:
            result = await populate_psalm_119()
            
            if result["status"] == "success":
                print(f"✅ SUCCESS: {result['message']}")
                print(f"📊 Letters created: {result['letters_created']}")
                print(f"📊 Verses created: {result['verses_created']}")
                
                verification = result["verification"]
                if verification["data_complete"]:
                    print("✅ Data integrity verification passed")
                else:
                    print("⚠️  Data integrity issues found:")
                    if verification["missing_verses"]:
                        print(f"   Missing verses: {verification['missing_verses']}")
                    if verification["orphaned_verses"]:
                        print(f"   Orphaned verses: {verification['orphaned_verses']}")
                        
                sys.exit(0)
            else:
                print(f"❌ ERROR: {result['message']}")
                sys.exit(1)
                
        except KeyboardInterrupt:
            print("\n⚠️  Migration interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"❌ FATAL ERROR: {str(e)}")
            sys.exit(1)
    
    # Run the migration
    asyncio.run(main())