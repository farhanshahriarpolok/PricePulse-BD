"""
Script to generate the complete 64-district Bangladesh spatial taxonomy
and GeoJSON centroid dataset.
"""

import json
from pathlib import Path

# Complete 8 Divisions and 64 Districts with coordinates and central markets
DIVISIONS_DATA = [
    {
        "name": "Dhaka",
        "bangla_name": "ঢাকা",
        "districts": [
            {
                "name": "Dhaka",
                "bangla_name": "ঢাকা",
                "lat": 23.8103, "lon": 90.4125,
                "markets": [
                    {"name": "Karwan Bazar", "bangla_name": "কারওয়ান বাজার", "type": "wholesale", "lat": 23.7516, "lon": 90.3944},
                    {"name": "Mirpur-1 Kacha Bazar", "bangla_name": "মিরপুর-১ কাঁচা বাজার", "type": "retail", "lat": 23.8067, "lon": 90.3541},
                    {"name": "Chaldal Online Hub", "bangla_name": "চালডাল অনলাইন হাব", "type": "online", "lat": 23.7808, "lon": 90.4192}
                ]
            },
            {
                "name": "Gazipur",
                "bangla_name": "গাজীপুর",
                "lat": 24.0023, "lon": 90.4264,
                "markets": [
                    {"name": "Joydebpur Central Bazar", "bangla_name": "জয়দেবপুর বাজার", "type": "retail", "lat": 23.9980, "lon": 90.4200},
                    {"name": "Tongi Wholesale Arat", "bangla_name": "টঙ্গী আড়ৎ", "type": "wholesale", "lat": 23.8960, "lon": 90.4020}
                ]
            },
            {
                "name": "Narayanganj",
                "bangla_name": "নারায়ণগঞ্জ",
                "lat": 23.6238, "lon": 90.5000,
                "markets": [
                    {"name": "Nitayganj Wholesale Arat", "bangla_name": "নিতাইগঞ্জ পাইকারি আড়ৎ", "type": "wholesale", "lat": 23.6150, "lon": 90.5050},
                    {"name": "Digubabur Bazar", "bangla_name": "দ্বিগুবাবুর বাজার", "type": "retail", "lat": 23.6220, "lon": 90.5010}
                ]
            },
            {
                "name": "Narsingdi",
                "bangla_name": "নরসিংদী",
                "lat": 23.9193, "lon": 90.7176,
                "markets": [
                    {"name": "Velanagar Bazar", "bangla_name": "ভেলারনগর বাজার", "type": "wholesale", "lat": 23.9210, "lon": 90.7150},
                    {"name": "Bhelanagar Retail Market", "bangla_name": "ভেলারনগর খুচরা বাজার", "type": "retail", "lat": 23.9180, "lon": 90.7200}
                ]
            },
            {
                "name": "Munshiganj",
                "bangla_name": "মুন্সীগঞ্জ",
                "lat": 23.5422, "lon": 90.5305,
                "markets": [
                    {"name": "Munshiganj Sadar Bazar", "bangla_name": "মুন্সীগঞ্জ সদর বাজার", "type": "retail", "lat": 23.5400, "lon": 90.5280},
                    {"name": "Mirkadim Potato Hub", "bangla_name": "মিরকাদিম আলুর আড়ৎ", "type": "wholesale", "lat": 23.5600, "lon": 90.5100}
                ]
            },
            {
                "name": "Manikganj",
                "bangla_name": "মানিকগঞ্জ",
                "lat": 23.8617, "lon": 90.0003,
                "markets": [
                    {"name": "Manikganj Bus Stand Bazar", "bangla_name": "মানিকগঞ্জ বাসস্ট্যান্ড বাজার", "type": "retail", "lat": 23.8600, "lon": 90.0020}
                ]
            },
            {
                "name": "Tangail",
                "bangla_name": "টাঙ্গাইল",
                "lat": 24.2513, "lon": 89.9167,
                "markets": [
                    {"name": "Park Bazar Tangail", "bangla_name": "পার্ক বাজার টাঙ্গাইল", "type": "wholesale", "lat": 24.2500, "lon": 89.9180}
                ]
            },
            {
                "name": "Kishoreganj",
                "bangla_name": "কিশোরগঞ্জ",
                "lat": 24.4449, "lon": 90.7766,
                "markets": [
                    {"name": "Borothakur Bazar", "bangla_name": "বড়বাজার কিশোরগঞ্জ", "type": "wholesale", "lat": 24.4410, "lon": 90.7790}
                ]
            },
            {
                "name": "Faridpur",
                "bangla_name": "ফরিদপুর",
                "lat": 23.6071, "lon": 89.8429,
                "markets": [
                    {"name": "Chawkbazar Faridpur", "bangla_name": "চকবাজার ফরিদপুর", "type": "wholesale", "lat": 23.6050, "lon": 89.8450}
                ]
            },
            {
                "name": "Gopalganj",
                "bangla_name": "গোপালগঞ্জ",
                "lat": 23.0051, "lon": 89.8266,
                "markets": [
                    {"name": "Gopalganj Sadar Bazar", "bangla_name": "গোপালগঞ্জ সদর বাজার", "type": "retail", "lat": 23.0040, "lon": 89.8250}
                ]
            },
            {
                "name": "Madaripur",
                "bangla_name": "মাদারীপুর",
                "lat": 23.1641, "lon": 90.1897,
                "markets": [
                    {"name": "Puran Bazar Madaripur", "bangla_name": "পুরান বাজার মাদারীপুর", "type": "retail", "lat": 23.1650, "lon": 90.1900}
                ]
            },
            {
                "name": "Rajbari",
                "bangla_name": "রাজবাড়ী",
                "lat": 23.7574, "lon": 89.6445,
                "markets": [
                    {"name": "Rajbari Railgate Bazar", "bangla_name": "রাজবাড়ী রেলগেট বাজার", "type": "retail", "lat": 23.7580, "lon": 89.6450}
                ]
            },
            {
                "name": "Shariatpur",
                "bangla_name": "শরীয়তপুর",
                "lat": 23.2423, "lon": 90.4348,
                "markets": [
                    {"name": "Palong Bazar", "bangla_name": "পালং বাজার", "type": "retail", "lat": 23.2410, "lon": 90.4330}
                ]
            }
        ]
    },
    {
        "name": "Chittagong",
        "bangla_name": "চট্টগ্রাম",
        "districts": [
            {
                "name": "Chattogram",
                "bangla_name": "চট্টগ্রাম",
                "lat": 22.3569, "lon": 91.7832,
                "markets": [
                    {"name": "Khatunganj", "bangla_name": "খাতুনগঞ্জ", "type": "wholesale", "lat": 22.3362, "lon": 91.8365},
                    {"name": "Reazuddin Bazar", "bangla_name": "রিয়াজউদ্দিন বাজার", "type": "retail", "lat": 22.3384, "lon": 91.8312}
                ]
            },
            {
                "name": "Cox's Bazar",
                "bangla_name": "কক্সবাজার",
                "lat": 21.4272, "lon": 92.0058,
                "markets": [
                    {"name": "Boro Bazar Cox's Bazar", "bangla_name": "বড় বাজার কক্সবাজার", "type": "wholesale", "lat": 21.4300, "lon": 92.0010}
                ]
            },
            {
                "name": "Cumilla",
                "bangla_name": "কুমিল্লা",
                "lat": 23.4682, "lon": 91.1788,
                "markets": [
                    {"name": "Chawkbazar Cumilla", "bangla_name": "চকবাজার কুমিল্লা", "type": "wholesale", "lat": 23.4650, "lon": 91.1800}
                ]
            },
            {
                "name": "Feni",
                "bangla_name": "ফেনী",
                "lat": 23.0159, "lon": 91.3976,
                "markets": [
                    {"name": "Feni Boro Bazar", "bangla_name": "ফেনী বড় বাজার", "type": "retail", "lat": 23.0170, "lon": 91.3980}
                ]
            },
            {
                "name": "Brahmanbaria",
                "bangla_name": "ব্রাহ্মণবাড়িয়া",
                "lat": 23.9571, "lon": 91.1119,
                "markets": [
                    {"name": "Anandabazar Brahmanbaria", "bangla_name": "আনন্দবাজার ব্রাহ্মণবাড়িয়া", "type": "retail", "lat": 23.9580, "lon": 91.1130}
                ]
            },
            {
                "name": "Noakhali",
                "bangla_name": "নোয়াখালী",
                "lat": 22.8696, "lon": 91.0994,
                "markets": [
                    {"name": "Maijdee Bazar", "bangla_name": "মাইজদী বাজার", "type": "retail", "lat": 22.8710, "lon": 91.0980}
                ]
            },
            {
                "name": "Chandpur",
                "bangla_name": "চাঁদপুর",
                "lat": 23.2333, "lon": 90.6667,
                "markets": [
                    {"name": "Hilsa Ghat Chandpur", "bangla_name": "ইলিশ ঘাট চাঁদপুর", "type": "wholesale", "lat": 23.2310, "lon": 90.6650}
                ]
            },
            {
                "name": "Lakshmipur",
                "bangla_name": "লক্ষ্মীপুর",
                "lat": 22.9425, "lon": 90.8412,
                "markets": [
                    {"name": "Lakshmipur Sadar Bazar", "bangla_name": "লক্ষ্মীপুর সদর বাজার", "type": "retail", "lat": 22.9430, "lon": 90.8420}
                ]
            },
            {
                "name": "Rangamati",
                "bangla_name": "রাঙ্গামাটি",
                "lat": 22.6574, "lon": 92.1733,
                "markets": [
                    {"name": "Banarupa Bazar", "bangla_name": "বনরূপা বাজার", "type": "retail", "lat": 22.6580, "lon": 92.1740}
                ]
            },
            {
                "name": "Khagrachhari",
                "bangla_name": "খাগড়াছড়ি",
                "lat": 23.1193, "lon": 91.9847,
                "markets": [
                    {"name": "Khagrachhari Sadar Bazar", "bangla_name": "খাগড়াছড়ি সদর বাজার", "type": "retail", "lat": 23.1200, "lon": 91.9850}
                ]
            },
            {
                "name": "Bandarban",
                "bangla_name": "বান্দরবান",
                "lat": 22.1953, "lon": 92.2184,
                "markets": [
                    {"name": "Madhyam Para Bazar", "bangla_name": "মধ্যম পাড়া বাজার", "type": "retail", "lat": 22.1960, "lon": 92.2190}
                ]
            }
        ]
    },
    {
        "name": "Rajshahi",
        "bangla_name": "রাজশাহী",
        "districts": [
            {
                "name": "Rajshahi",
                "bangla_name": "রাজশাহী",
                "lat": 24.3636, "lon": 88.6241,
                "markets": [
                    {"name": "Saheb Bazar Rajshahi", "bangla_name": "সাহেব বাজার রাজশাহী", "type": "wholesale", "lat": 24.3640, "lon": 88.6250},
                    {"name": "Masterpara Wholesale", "bangla_name": "মাস্টারপাড়া আড়ৎ", "type": "wholesale", "lat": 24.3620, "lon": 88.6230}
                ]
            },
            {
                "name": "Bogura",
                "bangla_name": "বগুড়া",
                "lat": 24.8465, "lon": 89.3770,
                "markets": [
                    {"name": "Raja Bazar Bogura", "bangla_name": "রাজাবাজার বগুড়া", "type": "wholesale", "lat": 24.8480, "lon": 89.3750},
                    {"name": "Phulbari Vegetable Arat", "bangla_name": "ফুলবাড়ি সবজি আড়ৎ", "type": "wholesale", "lat": 24.8520, "lon": 89.3790}
                ]
            },
            {
                "name": "Pabna",
                "bangla_name": "পাবনা",
                "lat": 24.0064, "lon": 89.2372,
                "markets": [
                    {"name": "Chhoto Bazar Pabna", "bangla_name": "ছোট বাজার পাবনা", "type": "retail", "lat": 24.0070, "lon": 89.2380}
                ]
            },
            {
                "name": "Sirajganj",
                "bangla_name": "সিরাজগঞ্জ",
                "lat": 24.4534, "lon": 89.7008,
                "markets": [
                    {"name": "Boro Bazar Sirajganj", "bangla_name": "বড় বাজার সিরাজগঞ্জ", "type": "wholesale", "lat": 24.4540, "lon": 89.7010}
                ]
            },
            {
                "name": "Naogaon",
                "bangla_name": "নওগাঁ",
                "lat": 24.7936, "lon": 88.9318,
                "markets": [
                    {"name": "Dakkhinchak Rice Arat", "bangla_name": "দক্ষিণচক চালের আড়ৎ", "type": "wholesale", "lat": 24.7950, "lon": 88.9330}
                ]
            },
            {
                "name": "Natore",
                "bangla_name": "নাটোর",
                "lat": 24.4206, "lon": 89.0003,
                "markets": [
                    {"name": "Nicho Bazar Natore", "bangla_name": "নিচো বাজার নাটোর", "type": "retail", "lat": 24.4210, "lon": 89.0010}
                ]
            },
            {
                "name": "Chapainawabganj",
                "bangla_name": "চাঁপাইনবাবগঞ্জ",
                "lat": 24.5965, "lon": 88.2775,
                "markets": [
                    {"name": "Puratan Bazar Chapai", "bangla_name": "পুরাতন বাজার চাঁপাই", "type": "wholesale", "lat": 24.5970, "lon": 88.2780}
                ]
            },
            {
                "name": "Joypurhat",
                "bangla_name": "জয়পুরহাট",
                "lat": 25.1015, "lon": 89.0277,
                "markets": [
                    {"name": "Joypurhat Central Bazar", "bangla_name": "জয়পুরহাট কেন্দ্রীয় বাজার", "type": "retail", "lat": 25.1020, "lon": 89.0280}
                ]
            }
        ]
    },
    {
        "name": "Khulna",
        "bangla_name": "খুলনা",
        "districts": [
            {
                "name": "Khulna",
                "bangla_name": "খুলনা",
                "lat": 22.8456, "lon": 89.5403,
                "markets": [
                    {"name": "Boro Bazar Khulna", "bangla_name": "বড় বাজার খুলনা", "type": "wholesale", "lat": 22.8460, "lon": 89.5410},
                    {"name": "Sandha Bazar", "bangla_name": "সন্ধ্যা বাজার খুলনা", "type": "retail", "lat": 22.8440, "lon": 89.5390}
                ]
            },
            {
                "name": "Jashore",
                "bangla_name": "যশোর",
                "lat": 23.1664, "lon": 89.2081,
                "markets": [
                    {"name": "Boro Bazar Jashore", "bangla_name": "বড় বাজার যশোর", "type": "wholesale", "lat": 23.1670, "lon": 89.2090}
                ]
            },
            {
                "name": "Satkhira",
                "bangla_name": "সাতক্ষীরা",
                "lat": 22.7185, "lon": 89.0705,
                "markets": [
                    {"name": "Sultanpur Fish & Fish Arat", "bangla_name": "সুলতানপুর মাছের আড়ৎ", "type": "wholesale", "lat": 22.7190, "lon": 89.0710}
                ]
            },
            {
                "name": "Bagerhat",
                "bangla_name": "বাগেরহাট",
                "lat": 22.6516, "lon": 89.7859,
                "markets": [
                    {"name": "Bagerhat Pradhan Bazar", "bangla_name": "বাগেরহাট প্রধান বাজার", "type": "retail", "lat": 22.6520, "lon": 89.7860}
                ]
            },
            {
                "name": "Jhenaidah",
                "bangla_name": "ঝিনাইদহ",
                "lat": 23.5448, "lon": 89.1539,
                "markets": [
                    {"name": "Jhenaidah Sadar Bazar", "bangla_name": "ঝিনাইদহ সদর বাজার", "type": "retail", "lat": 23.5450, "lon": 89.1540}
                ]
            },
            {
                "name": "Kushtia",
                "bangla_name": "কুষ্টিয়া",
                "lat": 23.9013, "lon": 89.1205,
                "markets": [
                    {"name": "Khajanagar Rice Mill Hub", "bangla_name": "খাজনগরের চালের আড়ৎ", "type": "wholesale", "lat": 23.9050, "lon": 89.1250}
                ]
            },
            {
                "name": "Chuadanga",
                "bangla_name": "চুয়াডাঙ্গা",
                "lat": 23.6402, "lon": 88.8418,
                "markets": [
                    {"name": "Chuadanga Boro Bazar", "bangla_name": "চুয়াডাঙ্গা বড় বাজার", "type": "retail", "lat": 23.6410, "lon": 88.8420}
                ]
            },
            {
                "name": "Meherpur",
                "bangla_name": "মেহেরপুর",
                "lat": 23.7622, "lon": 88.6318,
                "markets": [
                    {"name": "Meherpur Boro Bazar", "bangla_name": "মেহেরপুর বড় বাজার", "type": "retail", "lat": 23.7630, "lon": 88.6320}
                ]
            },
            {
                "name": "Magura",
                "bangla_name": "মাগুরা",
                "lat": 23.4873, "lon": 89.4199,
                "markets": [
                    {"name": "Chourangi Bazar Magura", "bangla_name": "চৌরঙ্গী বাজার মাগুরা", "type": "retail", "lat": 23.4880, "lon": 89.4200}
                ]
            },
            {
                "name": "Narail",
                "bangla_name": "নড়াইল",
                "lat": 23.1725, "lon": 89.5127,
                "markets": [
                    {"name": "Rupganj Bazar Narail", "bangla_name": "রূপগঞ্জ বাজার নড়াইল", "type": "retail", "lat": 23.1730, "lon": 89.5130}
                ]
            }
        ]
    },
    {
        "name": "Barisal",
        "bangla_name": "বরিশাল",
        "districts": [
            {
                "name": "Barishal",
                "bangla_name": "বরিশাল",
                "lat": 22.7010, "lon": 90.3535,
                "markets": [
                    {"name": "Port Road Wholesale Arat", "bangla_name": "পোর্ট রোড পাইকারি আড়ৎ", "type": "wholesale", "lat": 22.7020, "lon": 90.3540},
                    {"name": "Natun Bazar Barishal", "bangla_name": "নতুন বাজার বরিশাল", "type": "retail", "lat": 22.7000, "lon": 90.3520}
                ]
            },
            {
                "name": "Patuakhali",
                "bangla_name": "পটুয়াখালী",
                "lat": 22.3596, "lon": 90.3299,
                "markets": [
                    {"name": "Patuakhali Pouro Bazar", "bangla_name": "পটুয়াখালী পৌর বাজার", "type": "retail", "lat": 22.3600, "lon": 90.3300}
                ]
            },
            {
                "name": "Bhola",
                "bangla_name": "ভোলা",
                "lat": 22.6859, "lon": 90.6482,
                "markets": [
                    {"name": "Bhola Sadar Bazar", "bangla_name": "ভোলা সদর বাজার", "type": "retail", "lat": 22.6860, "lon": 90.6490}
                ]
            },
            {
                "name": "Pirojpur",
                "bangla_name": "পিরোজপুর",
                "lat": 22.5841, "lon": 89.9720,
                "markets": [
                    {"name": "Rajarhat Pirojpur", "bangla_name": "রাজারহাট পিরোজপুর", "type": "retail", "lat": 22.5850, "lon": 89.9730}
                ]
            },
            {
                "name": "Barguna",
                "bangla_name": "বরগুনা",
                "lat": 22.1587, "lon": 90.1256,
                "markets": [
                    {"name": "Barguna Launch Ghat Bazar", "bangla_name": "বরগুনা লঞ্চঘাট বাজার", "type": "retail", "lat": 22.1590, "lon": 90.1260}
                ]
            },
            {
                "name": "Jhalokati",
                "bangla_name": "ঝালকাঠি",
                "lat": 22.6406, "lon": 90.1987,
                "markets": [
                    {"name": "Bimruli Floating Market", "bangla_name": "ভিমরুলী ভাসমান বাজার", "type": "wholesale", "lat": 22.6420, "lon": 90.2000}
                ]
            }
        ]
    },
    {
        "name": "Sylhet",
        "bangla_name": "সিলেট",
        "districts": [
            {
                "name": "Sylhet",
                "bangla_name": "সিলেট",
                "lat": 24.8949, "lon": 91.8687,
                "markets": [
                    {"name": "Sobhanighat Wholesale Arat", "bangla_name": "সোবহানীঘাট আড়ৎ", "type": "wholesale", "lat": 24.8960, "lon": 91.8700},
                    {"name": "Bondor Bazar Sylhet", "bangla_name": "বন্দর বাজার সিলেট", "type": "retail", "lat": 24.8930, "lon": 91.8670}
                ]
            },
            {
                "name": "Moulvibazar",
                "bangla_name": "মৌলভীবাজার",
                "lat": 24.4829, "lon": 91.7774,
                "markets": [
                    {"name": "Paschim Bazar Moulvibazar", "bangla_name": "পশ্চিম বাজার মৌলভীবাজার", "type": "retail", "lat": 24.4840, "lon": 91.7780}
                ]
            },
            {
                "name": "Habiganj",
                "bangla_name": "হবিগঞ্জ",
                "lat": 24.3749, "lon": 91.4155,
                "markets": [
                    {"name": "Chowdhury Bazar Habiganj", "bangla_name": "চৌধুরী বাজার হবিগঞ্জ", "type": "retail", "lat": 24.3760, "lon": 91.4160}
                ]
            },
            {
                "name": "Sunamganj",
                "bangla_name": "সুনামগঞ্জ",
                "lat": 25.0658, "lon": 91.3950,
                "markets": [
                    {"name": "Madhyanagar Fish Arat", "bangla_name": "মধ্যনগর মাছের আড়ৎ", "type": "wholesale", "lat": 25.0670, "lon": 91.3960}
                ]
            }
        ]
    },
    {
        "name": "Rangpur",
        "bangla_name": "রংপুর",
        "districts": [
            {
                "name": "Rangpur",
                "bangla_name": "রংপুর",
                "lat": 25.7439, "lon": 89.2752,
                "markets": [
                    {"name": "City Bazar Rangpur", "bangla_name": "সিটি বাজার রংপুর", "type": "wholesale", "lat": 25.7450, "lon": 89.2760},
                    {"name": "Nababganj Bazar", "bangla_name": "নবাবগঞ্জ বাজার রংপুর", "type": "retail", "lat": 25.7420, "lon": 89.2740}
                ]
            },
            {
                "name": "Dinajpur",
                "bangla_name": "দিনাজপুর",
                "lat": 25.6217, "lon": 88.6355,
                "markets": [
                    {"name": "Bahadur Bazar Dinajpur", "bangla_name": "বাহাদুর বাজার দিনাজপুর", "type": "wholesale", "lat": 25.6230, "lon": 88.6360}
                ]
            },
            {
                "name": "Kurigram",
                "bangla_name": "কুড়িগ্রাম",
                "lat": 25.8054, "lon": 89.6362,
                "markets": [
                    {"name": "Pouro Bazar Kurigram", "bangla_name": "পৌর বাজার কুড়িগ্রাম", "type": "retail", "lat": 25.8060, "lon": 89.6370}
                ]
            },
            {
                "name": "Gaibandha",
                "bangla_name": "গাইবান্ধা",
                "lat": 25.3288, "lon": 89.5403,
                "markets": [
                    {"name": "Puratan Bazar Gaibandha", "bangla_name": "পুরাতন বাজার গাইবান্ধা", "type": "retail", "lat": 25.3290, "lon": 89.5410}
                ]
            },
            {
                "name": "Nilphamari",
                "bangla_name": "নীলফামারী",
                "lat": 25.9318, "lon": 88.8560,
                "markets": [
                    {"name": "Saidpur Rail Market", "bangla_name": "সৈয়দপুর রেল বাজার", "type": "wholesale", "lat": 25.7780, "lon": 88.8920}
                ]
            },
            {
                "name": "Lalmonirhat",
                "bangla_name": "লালমনিরহাট",
                "lat": 25.9923, "lon": 89.2847,
                "markets": [
                    {"name": "Goshala Bazar Lalmonirhat", "bangla_name": "গোশালা বাজার লালমনিরহাট", "type": "retail", "lat": 25.9930, "lon": 89.2850}
                ]
            },
            {
                "name": "Thakurgaon",
                "bangla_name": "ঠাকুরগাঁও",
                "lat": 26.0337, "lon": 88.4617,
                "markets": [
                    {"name": "Kalibari Bazar Thakurgaon", "bangla_name": "কালিবাড়ি বাজার ঠাকুরগাঁও", "type": "retail", "lat": 26.0350, "lon": 88.4620}
                ]
            },
            {
                "name": "Panchagarh",
                "bangla_name": "পঞ্চগড়",
                "lat": 26.3411, "lon": 88.5542,
                "markets": [
                    {"name": "Panchagarh Bazar", "bangla_name": "পঞ্চগড় বাজার", "type": "retail", "lat": 26.3420, "lon": 88.5550}
                ]
            }
        ]
    },
    {
        "name": "Mymensingh",
        "bangla_name": "ময়মনসিংহ",
        "districts": [
            {
                "name": "Mymensingh",
                "bangla_name": "ময়মনসিংহ",
                "lat": 24.7471, "lon": 90.4203,
                "markets": [
                    {"name": "Mechuabazar Wholesale Arat", "bangla_name": "মেছুয়াবাজার আড়ৎ", "type": "wholesale", "lat": 24.7480, "lon": 90.4210},
                    {"name": "Natun Bazar Mymensingh", "bangla_name": "নতুন বাজার ময়মনসিংহ", "type": "retail", "lat": 24.7460, "lon": 90.4190}
                ]
            },
            {
                "name": "Jamalpur",
                "bangla_name": "জামালপুর",
                "lat": 24.9375, "lon": 89.9378,
                "markets": [
                    {"name": "Station Bazar Jamalpur", "bangla_name": "স্টেশন বাজার জামালপুর", "type": "retail", "lat": 24.9380, "lon": 89.9380}
                ]
            },
            {
                "name": "Netrokona",
                "bangla_name": "নেত্রকোণা",
                "lat": 24.8709, "lon": 90.7279,
                "markets": [
                    {"name": "Chhoto Bazar Netrokona", "bangla_name": "ছোট বাজার নেত্রকোণা", "type": "retail", "lat": 24.8720, "lon": 90.7290}
                ]
            },
            {
                "name": "Sherpur",
                "bangla_name": "শেরপুর",
                "lat": 25.0205, "lon": 90.0153,
                "markets": [
                    {"name": "Nayanbazar Sherpur", "bangla_name": "নয়নবাজার শেরপুর", "type": "retail", "lat": 25.0210, "lon": 90.0160}
                ]
            }
        ]
    }
]

def build_locations_json():
    root = Path(__file__).resolve().parent.parent
    loc_file = root / "data" / "taxonomy" / "locations.json"
    data = {"divisions": []}

    total_districts = 0
    total_markets = 0

    for div in DIVISIONS_DATA:
        div_entry = {
            "name": div["name"],
            "bangla_name": div["bangla_name"],
            "districts": []
        }
        for dist in div["districts"]:
            total_districts += 1
            mkt_list = []
            for m in dist["markets"]:
                total_markets += 1
                mkt_list.append({
                    "name": m["name"],
                    "bangla_name": m["bangla_name"],
                    "market_type": m["type"],
                    "latitude": m["lat"],
                    "longitude": m["lon"]
                })
            div_entry["districts"].append({
                "name": dist["name"],
                "bangla_name": dist["bangla_name"],
                "latitude": dist["lat"],
                "longitude": dist["lon"],
                "markets": mkt_list
            })
        data["divisions"].append(div_entry)

    with open(loc_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Generated {loc_file}: {len(data['divisions'])} divisions, {total_districts} districts, {total_markets} markets.")

def build_geojson():
    root = Path(__file__).resolve().parent.parent
    geo_file = root / "data" / "geo" / "bangladesh_districts_simplified.json"

    features = []
    fid = 1

    for div in DIVISIONS_DATA:
        for dist in div["districts"]:
            features.append({
                "type": "Feature",
                "properties": {
                    "id": fid,
                    "name": dist["name"],
                    "bn_name": dist["bangla_name"],
                    "division": div["name"],
                    "latitude": dist["lat"],
                    "longitude": dist["lon"],
                    "primary_market": dist["markets"][0]["name"] if dist["markets"] else "Sadar Bazar"
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [dist["lon"], dist["lat"]]
                }
            })
            fid += 1

    geojson_data = {
        "type": "FeatureCollection",
        "name": "bangladesh_districts_simplified",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
        },
        "features": features
    }

    with open(geo_file, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f, indent=2, ensure_ascii=False)
    print(f"Generated {geo_file}: {len(features)} district features.")

if __name__ == "__main__":
    build_locations_json()
    build_geojson()
