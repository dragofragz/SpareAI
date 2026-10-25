"""
seed.py — Comprehensive realistic database seeder for SpareAI.

Populates:
  - Demo user (demo@example.com / demo123) with Hyundai i20 and RE Classic 350
  - Admin user (admin@example.com / admin123)
  - 5 Suppliers around Cherthala, Alappuzha, and Kochi
  - 6 Workshops around Cherthala, Alappuzha, and Kochi
  - 32 Spare Parts with OEM codes, INR pricing, stock levels, and YouTube video IDs
  - Vehicle compatibilities across popular Indian cars and two-wheelers
  - 70+ historical RepairCases with SBERT embeddings pre-computed and stored as BLOBs
"""

import sys
import os
import numpy as np
from werkzeug.security import generate_password_hash

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base, SessionLocal
from app.models import (
    User, Vehicle, Supplier, Workshop,
    SparePart, PartCompatibility, RepairCase
)
from app.ai_engine import encode_text


def seed():
    print("[Seed] Resetting and creating database schema...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # -------------------------------------------------------------------
        # 1. Users & Initial Vehicles
        # -------------------------------------------------------------------
        print("[Seed] Creating demo and admin users...")
        demo_user = User(
            name="Rahul Nair",
            email="demo@example.com",
            password_hash=generate_password_hash("demo123", method="pbkdf2:sha256"),
            contact="+91 98470 12345",
            address="Near KSRTC Bus Stand, Cherthala, Alappuzha, Kerala - 688524",
            role="customer",
            is_admin=False,
        )
        admin_user = User(
            name="System Administrator",
            email="admin@example.com",
            password_hash=generate_password_hash("admin123", method="pbkdf2:sha256"),
            contact="+91 94471 99999",
            address="SpareAI Enterprise Core Operations, Cherthala Hub",
            role="admin",
            is_admin=True,
        )
        db.add_all([demo_user, admin_user])
        db.flush()

        v1 = Vehicle(
            user_id=demo_user.user_id,
            type="car",
            make="Hyundai",
            model="i20",
            year=2020,
            vin="MALBA51BLM123456",
        )
        v2 = Vehicle(
            user_id=demo_user.user_id,
            type="bike",
            make="Royal Enfield",
            model="Classic 350",
            year=2019,
            vin="ME3U3S5C0KL654321",
        )
        db.add_all([v1, v2])
        db.flush()

        # -------------------------------------------------------------------
        # 2. Suppliers (Cherthala, Alappuzha, Kochi)
        # -------------------------------------------------------------------
        print("[Seed] Creating suppliers...")
        suppliers = [
            Supplier(
                supplier_id=1,
                name="Cherthala Auto Spares & Distributor",
                lat=9.6885,
                lng=76.3320,
                address="Court Junction, Cherthala, Kerala 688524",
                contact="+91 478 2812345",
            ),
            Supplier(
                supplier_id=2,
                name="Alappuzha Motor Hub",
                lat=9.4981,
                lng=76.3388,
                address="Boat Jetty Road, Alappuzha, Kerala 688001",
                contact="+91 477 2254321",
            ),
            Supplier(
                supplier_id=3,
                name="Kochi Genuine Parts Depot",
                lat=9.9816,
                lng=76.2999,
                address="MG Road, Ernakulam, Kochi, Kerala 682016",
                contact="+91 484 2367890",
            ),
            Supplier(
                supplier_id=4,
                name="Vytilla Automotive Logistics",
                lat=9.9658,
                lng=76.3204,
                address="Mobility Hub Bypass, Vytilla, Kochi 682019",
                contact="+91 484 2781122",
            ),
            Supplier(
                supplier_id=5,
                name="Mararikulam Two-Wheeler Spares",
                lat=9.6012,
                lng=76.3120,
                address="Mararikkulam North, Alappuzha 688523",
                contact="+91 478 2865432",
            ),
        ]
        db.add_all(suppliers)
        db.flush()

        # Create dedicated supplier user linked to Cherthala Auto Spares
        supplier_user = User(
            name="K. V. Raman (Cherthala Auto Spares)",
            email="supplier@example.com",
            password_hash=generate_password_hash("supplier123", method="pbkdf2:sha256"),
            contact="+91 478 2812345",
            address="Court Junction, Cherthala, Kerala 688524",
            role="supplier",
            is_admin=False,
            supplier_id=1,
        )
        db.add(supplier_user)
        db.flush()

        # -------------------------------------------------------------------
        # 3. Workshops (Cherthala, Alappuzha, Kochi)
        # -------------------------------------------------------------------
        print("[Seed] Creating workshops...")
        workshops = [
            Workshop(
                workshop_id=1,
                name="Cherthala Modern Car Care",
                lat=9.6845,
                lng=76.3362,
                address="Near Civil Station, Cherthala 688524",
                contact="+91 98471 22334",
                verified=True,
                rating=4.8,
            ),
            Workshop(
                workshop_id=2,
                name="Coastal Auto Garage",
                lat=9.6920,
                lng=76.3280,
                address="Arthunkal Bypass Road, Cherthala 688524",
                contact="+91 94462 33445",
                verified=True,
                rating=4.5,
            ),
            Workshop(
                workshop_id=3,
                name="Alappuzha Precision Motors",
                lat=9.5010,
                lng=76.3420,
                address="Cullen Road, Alappuzha 688012",
                contact="+91 94473 44556",
                verified=True,
                rating=4.7,
            ),
            Workshop(
                workshop_id=4,
                name="Kochi Elite Auto Works",
                lat=9.9920,
                lng=76.3050,
                address="Palarivattom Bypass, Kochi 682025",
                contact="+91 98460 55667",
                verified=True,
                rating=4.9,
            ),
            Workshop(
                workshop_id=5,
                name="Vembanad Two-Wheeler Clinic",
                lat=9.6720,
                lng=76.3450,
                address="Muhamma Road, Cherthala South 688539",
                contact="+91 94465 66778",
                verified=True,
                rating=4.6,
            ),
            Workshop(
                workshop_id=6,
                name="National Speed Workshop",
                lat=9.9550,
                lng=76.3150,
                address="Kundannoor Junction, Maradu, Kochi 682304",
                contact="+91 98475 77889",
                verified=False,
                rating=4.2,
            ),
        ]
        db.add_all(workshops)
        db.flush()

        # -------------------------------------------------------------------
        # 4. Spare Parts (32 parts, cars & bikes, with video IDs and prices)
        # -------------------------------------------------------------------
        print("[Seed] Creating spare parts catalog...")
        parts_data = [
            # 1: Lower Control Arm
            (1, "Front Lower Control Arm Suspension Assembly", "HYU-54500-1J000", 2850.0, "Suspension", 1, 0,
             "https://images.unsplash.com/photo-1486006920555-c77dce18193b", "V_g1-WHD4rw", "Hard",
             "Ball joint separator, 17mm/19mm socket, torque wrench, floor jack, jack stands"),
            # 2: Front Shock Absorber
            (2, "Front Gas Shock Absorber Strut", "HYU-54651-C8000", 3200.0, "Suspension", 2, 8,
             "https://images.unsplash.com/photo-1486006920555-c77dce18193b", "V_g1-WHD4rw", "Hard",
             "Spring compressor, 14mm/17mm spanners, strut nut socket, jack"),
            # 3: Ball Joint
            (3, "Front Suspension Lower Ball Joint", "BJ-HY-2015", 850.0, "Suspension", 1, 14,
             "https://images.unsplash.com/photo-1486006920555-c77dce18193b", "aPbL9HTHZg0", "Medium",
             "Ball joint puller, retaining ring pliers, socket set"),
            # 4: Brake Pads
            (4, "Front Ceramic Brake Pad Set", "BP-HY-58101", 1450.0, "Braking", 3, 20,
             "https://images.unsplash.com/photo-1486006920555-c77dce18193b", "6RQ9UabOIPg", "Medium",
             "C-clamp or caliper piston spreader, 14mm ratchet, brake cleaner"),
            # 5: Brake Disc Rotor
            (5, "Front Ventilated Brake Disc Rotor", "BR-51712-C8000", 2200.0, "Braking", 1, 5,
             "https://images.unsplash.com/photo-1486006920555-c77dce18193b", "6RQ9UabOIPg", "Medium",
             "Impact screwdriver, 17mm socket, wire brush"),
            # 6: Clutch Plate Kit (Car)
            (6, "Clutch Pressure Plate & Friction Disc Kit", "CK-HYU-41100", 4800.0, "Transmission", 4, 3,
             "https://images.unsplash.com/photo-1486006920555-c77dce18193b", "QcWELyTbdP4", "Hard",
             "Clutch alignment tool, transmission jack, complete metric socket set"),
            # 7: 12V 45Ah Automotive Battery
            (7, "12V 45Ah Maintenance-Free Car Battery", "BAT-EX-45L", 4200.0, "Electrical", 1, 12,
             "https://images.unsplash.com/photo-1486006920555-c77dce18193b", "COJr7OB23Hw", "Easy",
             "10mm wrench, terminal cleaner, battery terminal grease"),
            # 8: Alternator Assembly
            (8, "12V 90A Alternator Assembly", "ALT-HY-37300", 6800.0, "Electrical", 3, 4,
             "https://images.unsplash.com/photo-1486006920555-c77dce18193b", "LGB6ZEjGm7Q", "Hard",
             "Serpentine belt tool, 12mm/14mm sockets, multimeter"),
            # 9: Iridium Spark Plug (4-pack)
            (9, "Iridium Spark Plug Set (Pack of 4)", "SP-NGK-LZKR6B", 1200.0, "Engine", 2, 25,
             "https://images.unsplash.com/photo-1486006920555-c77dce18193b", "ngQh0xd5_CA", "Easy",
             "16mm spark plug socket, extension bar, ratchet, gap gauge"),
            # 10: Engine Air Filter
            (10, "High-Flow Engine Air Filter", "AF-28113-C8000", 450.0, "Filters", 1, 30,
             "https://images.unsplash.com/photo-1486006920555-c77dce18193b", "O1hF25Cowv8", "Easy",
             "None (clip-on housing)"),
            # 11: Spin-on Oil Filter
            (11, "Spin-On Engine Oil Filter", "OF-26300-35505", 280.0, "Filters", 1, 40,
             "https://images.unsplash.com/photo-1486006920555-c77dce18193b", "O1hF25Cowv8", "Easy",
             "Oil filter wrench, drain pan, 17mm socket"),
            # 12: Timing Belt / Chain Kit
            (12, "Engine Timing Chain & Tensioner Kit", "TC-HY-24321", 5400.0, "Engine", 4, 2,
             "https://images.unsplash.com/photo-1486006920555-c77dce18193b", "QcWELyTbdP4", "Hard",
             "Camshaft locking tool, crankshaft pulley puller, torque wrench"),
            # 13: Halogen H4 Headlight Bulb
            (13, "H4 12V 60/55W Headlight Halogen Bulb", "BULB-H4-PH12", 220.0, "Lighting", 1, 50,
             "https://images.unsplash.com/photo-1486006920555-c77dce18193b", "6RQ9UabOIPg", "Easy",
             "Gloves (do not touch quartz glass directly)"),
            # 14: Aluminum Radiator Core
            (14, "Aluminum Engine Cooling Radiator", "RAD-HY-25310", 3600.0, "Cooling", 3, 4,
             "https://images.unsplash.com/photo-1486006920555-c77dce18193b", "MeruAZebIeU", "Hard",
             "Hose clamp pliers, 10mm socket, coolant catch basin, funnel"),
            # 15: Windshield Wiper Motor & Linkage
            (15, "Front Windshield Wiper Motor & Linkage", "WM-98110-C8000", 2100.0, "Electrical", 2, 6,
             "https://images.unsplash.com/photo-1486006920555-c77dce18193b", "O1hF25Cowv8", "Medium",
             "14mm wiper arm puller, cowl trim clip tool, 10mm ratchet"),
            # 16: Steering Tie Rod End
            (16, "Front Steering Outer Tie Rod End", "TR-56820-C8000", 650.0, "Steering", 1, 15,
             "https://images.unsplash.com/photo-1486006920555-c77dce18193b", "_3RjhtVse6jE", "Medium",
             "Tie rod separator tool, 19mm/21mm wrench, cotter pin pliers"),
            # 17: Front Wheel Bearing Hub
            (17, "Front Wheel Hub & Sealed Bearing Unit", "WB-51750-C8000", 1750.0, "Drivetrain", 4, 7,
             "https://images.unsplash.com/photo-1486006920555-c77dce18193b", "fe_WtKIKlYA", "Hard",
             "32mm axle nut socket, breaker bar, slide hammer or hydraulic press"),
            # 18: Engine Water Pump
            (18, "Engine Coolant Water Pump Assembly", "WP-25100-2B700", 1650.0, "Cooling", 3, 9,
             "https://images.unsplash.com/photo-1486006920555-c77dce18193b", "5-V2OuceQkY", "Hard",
             "Gasket scraper, 10mm/12mm sockets, torque wrench, RTV sealant"),
            # 19: Fuel Pump Motor & Strainer
            (19, "In-Tank Electric Fuel Pump Motor", "FP-31111-C8000", 2900.0, "Fuel System", 2, 5,
             "https://images.unsplash.com/photo-1486006920555-c77dce18193b", "COJr7OB23Hw", "Hard",
             "Fuel tank lock ring tool, brass punch, hose disconnect tools"),
            # 20: Ignition Coil Pack
            (20, "Electronic Ignition Coil Pack", "IC-27301-2B010", 1850.0, "Electrical", 1, 11,
             "https://images.unsplash.com/photo-1486006920555-c77dce18193b", "ngQh0xd5_CA", "Easy",
             "10mm socket, dielectric grease"),

            # ----------------- BIKE PARTS -----------------
            # 21: Drive Chain & Sprocket Kit (Bike)
            (21, "Heavy-Duty Drive Chain & Sprocket Kit", "RE-57123-CSK", 2400.0, "Transmission", 5, 12,
             "https://images.unsplash.com/photo-1558981403-c5f9899a28bc", "MHsexh8_kKs", "Medium",
             "Chain breaker/riveter tool, 24mm/27mm axle wrench, 10mm socket"),
            # 22: Motorcycle Clutch Cable & Plates Kit
            (22, "Motorcycle Wet Clutch Friction Plate Kit", "RE-CLU-350CP", 1150.0, "Transmission", 5, 8,
             "https://images.unsplash.com/photo-1558981403-c5f9899a28bc", "R9oD6cZ7V_4", "Medium",
             "Clutch holding tool, 8mm T-handle, fresh engine oil for soaking plates"),
            # 23: Throttle Accelerator Cable (Bike)
            (23, "Teflon-Coated Throttle Accelerator Cable", "TH-CAB-RE350", 280.0, "Controls", 5, 20,
             "https://images.unsplash.com/photo-1558981403-c5f9899a28bc", "MHsexh8_kKs", "Easy",
             "Phillips screwdriver, 10mm open spanner, cable lube"),
            # 24: Rear Tail Light Assembly / Lens (Bike)
            (24, "Vintage Style Rear Tail Light Assembly", "TL-RE-VINT-01", 650.0, "Lighting", 5, 15,
             "https://images.unsplash.com/photo-1558981403-c5f9899a28bc", "1xITumgvvS4", "Easy",
             "10mm spanner, wire stripper/crimper"),
            # 25: Bike Disc Brake Pad Set
            (25, "Rear/Front Sintered Disc Brake Pads (Bike)", "BP-BYBRE-M100", 550.0, "Braking", 5, 18,
             "https://images.unsplash.com/photo-1558981403-c5f9899a28bc", "1xITumgvvS4", "Easy",
             "5mm Allen key, flat screwdriver, needle-nose pliers"),
            # 26: 12V 14Ah Motorcycle Battery
            (26, "12V 14Ah VRLA Motorcycle Battery", "BAT-AM-PRO14", 2600.0, "Electrical", 1, 9,
             "https://images.unsplash.com/photo-1558981403-c5f9899a28bc", "COJr7OB23Hw", "Easy",
             "Phillips screwdriver, 10mm wrench"),
            # 27: Bike Rear Gas Shock Absorbers (Pair)
            (27, "Twin Rear Gas Charged Shock Absorbers", "SA-RE-TWIN-G", 3400.0, "Suspension", 5, 6,
             "https://images.unsplash.com/photo-1558981403-c5f9899a28bc", "pQ72u9wT5rq", "Medium",
             "14mm and 17mm socket/ring spanners, center stand"),
            # 28: Bike Spark Plug
            (28, "Resistor Type Single Spark Plug", "SP-NGK-CPR8EA", 180.0, "Engine", 2, 45,
             "https://images.unsplash.com/photo-1558981403-c5f9899a28bc", "ngQh0xd5_CA", "Easy",
             "16mm spark plug spanner"),
            # 29: Bike Front Fork Oil Seal & Dust Cap Kit
            (29, "Front Fork Oil Seal & Dust Boot Set", "FS-41MM-RE01", 380.0, "Suspension", 5, 10,
             "https://images.unsplash.com/photo-1558981403-c5f9899a28bc", "pQ72u9wT5rq", "Hard",
             "Fork seal driver, circlip pliers, Allen key socket set, fork oil"),
            # 30: Bike Carburetor / Fuel Injector Cleaner Kit
            (30, "Electronic Fuel Injector & Sensor Assembly", "FI-RE-350BS6", 2150.0, "Fuel System", 5, 5,
             "https://images.unsplash.com/photo-1558981403-c5f9899a28bc", "MHsexh8_kKs", "Medium",
             "10mm socket, hex keys, carburetor cleaner"),
            # 31: Lower Control Arm (Second supplier listing - for multi-supplier stock demo!)
            (31, "Front Lower Control Arm Suspension Assembly", "HYU-54500-1J000", 2850.0, "Suspension", 3, 6,
             "https://images.unsplash.com/photo-1486006920555-c77dce18193b", "V_g1-WHD4rw", "Hard",
             "Ball joint separator, 17mm/19mm socket, torque wrench, floor jack"),
            # 32: Lower Control Arm (Third supplier listing - 0 stock)
            (32, "Front Lower Control Arm Suspension Assembly", "HYU-54500-1J000", 2900.0, "Suspension", 2, 0,
             "https://images.unsplash.com/photo-1486006920555-c77dce18193b", "V_g1-WHD4rw", "Hard",
             "Ball joint separator, 17mm/19mm socket, torque wrench"),
        ]

        for p in parts_data:
            sp = SparePart(
                part_id=p[0],
                part_name=p[1],
                oem_code=p[2],
                price=p[3],
                category=p[4],
                supplier_id=p[5],
                stock_qty=p[6],
                image_url=p[7],
                video_id=p[8],
                difficulty=p[9],
                tools_required=p[10],
            )
            db.add(sp)
        db.flush()

        # -------------------------------------------------------------------
        # 5. Part Compatibilities (cars & bikes across models & year ranges)
        # -------------------------------------------------------------------
        print("[Seed] Creating vehicle fitment compatibilities...")
        compat_data = [
            # Part 1, 31, 32: Lower Control Arm (Hyundai i20)
            (1, "Hyundai", "i20", 2014, 2024),
            (1, "Hyundai", "Grand i10", 2013, 2022),
            (31, "Hyundai", "i20", 2014, 2024),
            (32, "Hyundai", "i20", 2014, 2024),
            # Part 2: Shock Absorber (Hyundai i20, Maruti Swift)
            (2, "Hyundai", "i20", 2015, 2024),
            (2, "Maruti", "Swift", 2015, 2023),
            # Part 3: Ball Joint
            (3, "Hyundai", "i20", 2012, 2024),
            (3, "Maruti", "Swift", 2014, 2023),
            (3, "Honda", "City", 2014, 2022),
            # Part 4: Brake Pads
            (4, "Hyundai", "i20", 2014, 2024),
            (4, "Hyundai", "Verna", 2015, 2023),
            (4, "Maruti", "Swift", 2015, 2024),
            (4, "Honda", "City", 2014, 2023),
            # Part 5: Brake Disc
            (5, "Hyundai", "i20", 2015, 2024),
            (5, "Maruti", "Swift", 2015, 2023),
            # Part 6: Clutch Kit
            (6, "Hyundai", "i20", 2014, 2023),
            (6, "Maruti", "Swift", 2012, 2022),
            # Part 7: Battery
            (7, "Hyundai", "i20", 2010, 2024),
            (7, "Maruti", "Swift", 2010, 2024),
            (7, "Honda", "City", 2010, 2024),
            # Part 8: Alternator
            (8, "Hyundai", "i20", 2014, 2023),
            (8, "Maruti", "Swift", 2014, 2023),
            # Part 9: Spark Plugs
            (9, "Hyundai", "i20", 2014, 2024),
            (9, "Maruti", "Swift", 2012, 2024),
            (9, "Honda", "City", 2012, 2024),
            # Part 10: Air Filter
            (10, "Hyundai", "i20", 2016, 2024),
            (10, "Maruti", "Swift", 2017, 2024),
            # Part 11: Oil Filter
            (11, "Hyundai", "i20", 2012, 2024),
            (11, "Maruti", "Swift", 2012, 2024),
            (11, "Honda", "City", 2012, 2024),
            # Part 12: Timing Chain
            (12, "Hyundai", "i20", 2015, 2023),
            (12, "Maruti", "Swift", 2014, 2022),
            # Part 13: Headlight Bulb
            (13, "Hyundai", "i20", 2010, 2024),
            (13, "Maruti", "Swift", 2010, 2024),
            (13, "Royal Enfield", "Classic 350", 2012, 2024),
            # Part 14: Radiator
            (14, "Hyundai", "i20", 2015, 2023),
            (14, "Maruti", "Swift", 2015, 2023),
            # Part 15: Wiper Motor
            (15, "Hyundai", "i20", 2014, 2023),
            (15, "Maruti", "Swift", 2014, 2023),
            # Part 16: Tie Rod
            (16, "Hyundai", "i20", 2014, 2024),
            (16, "Maruti", "Swift", 2014, 2024),
            # Part 17: Wheel Bearing
            (17, "Hyundai", "i20", 2014, 2024),
            (17, "Maruti", "Swift", 2014, 2024),
            # Part 18: Water Pump
            (18, "Hyundai", "i20", 2014, 2023),
            # Part 19: Fuel Pump
            (19, "Hyundai", "i20", 2014, 2023),
            # Part 20: Ignition Coil
            (20, "Hyundai", "i20", 2014, 2024),

            # Bikes Compatibilities (Royal Enfield Classic 350, Pulsar, Apache, Activa)
            # Part 21: Chain Sprocket Kit
            (21, "Royal Enfield", "Classic 350", 2012, 2024),
            (21, "Royal Enfield", "Bullet 350", 2012, 2024),
            (21, "Bajaj", "Pulsar 150", 2015, 2024),
            # Part 22: Bike Clutch Plates
            (22, "Royal Enfield", "Classic 350", 2012, 2024),
            (22, "Royal Enfield", "Bullet 350", 2012, 2024),
            (22, "TVS", "Apache RTR", 2016, 2024),
            # Part 23: Throttle Cable
            (23, "Royal Enfield", "Classic 350", 2010, 2024),
            (23, "Bajaj", "Pulsar 150", 2012, 2024),
            # Part 24: Tail Light
            (24, "Royal Enfield", "Classic 350", 2010, 2024),
            (24, "Royal Enfield", "Bullet 350", 2010, 2024),
            # Part 25: Bike Brake Pads
            (25, "Royal Enfield", "Classic 350", 2016, 2024),
            (25, "Bajaj", "Pulsar 150", 2015, 2024),
            (25, "TVS", "Apache RTR", 2016, 2024),
            # Part 26: Bike Battery
            (26, "Royal Enfield", "Classic 350", 2010, 2024),
            (26, "Bajaj", "Pulsar 150", 2014, 2024),
            (26, "Honda", "Activa 6G", 2015, 2024),
            # Part 27: Rear Shocks
            (27, "Royal Enfield", "Classic 350", 2010, 2024),
            (27, "Royal Enfield", "Bullet 350", 2010, 2024),
            # Part 28: Bike Spark Plug
            (28, "Royal Enfield", "Classic 350", 2012, 2024),
            (28, "Bajaj", "Pulsar 150", 2012, 2024),
            (28, "Honda", "Activa 6G", 2015, 2024),
            # Part 29: Fork Seals
            (29, "Royal Enfield", "Classic 350", 2012, 2024),
            # Part 30: Fuel Injector
            (30, "Royal Enfield", "Classic 350", 2019, 2024),
        ]

        for c in compat_data:
            pc = PartCompatibility(
                part_id=c[0],
                make=c[1],
                model=c[2],
                year_from=c[3],
                year_to=c[4],
            )
            db.add(pc)
        db.flush()

        # -------------------------------------------------------------------
        # 6. Historical Repair Cases (70+ cases covering cars & bikes)
        # -------------------------------------------------------------------
        print("[Seed] Creating CBR historical repair cases (70+ cases)...")
        cases_raw = [
            # CAR: Lower Control Arm (Part 1)
            ("Loud grinding and knocking noise from underbody when turning over speed bumps", "car", "Hyundai", "i20", 1),
            ("Clunking metallic thud from front suspension when going over rough potholes and uneven roads", "car", "Hyundai", "i20", 1),
            ("Vibration in steering wheel and steering wander with dull clunk when taking sharp turns", "car", "Hyundai", "i20", 1),
            ("Front suspension bushing torn, severe knocking sound underneath car on speed breakers", "car", "Maruti", "Swift", 1),

            # CAR: Front Shock Absorber (Part 2)
            ("Car continues bouncing excessively after bumps and feels unstable at highway speeds", "car", "Hyundai", "i20", 2),
            ("Fluid leaking from front wheel strut and harsh jarring ride over minor road imperfections", "car", "Hyundai", "i20", 2),
            ("Vehicle nose-dives heavily forward under moderate braking with loud bottoming out thud", "car", "Maruti", "Swift", 2),

            # CAR: Ball Joint (Part 3)
            ("High-pitched squeaking noise from front wheel area when turning steering wheel slowly while parking", "car", "Hyundai", "i20", 3),
            ("Steering feels loose and disconnected with sudden snap noise when turning sharply into driveway", "car", "Hyundai", "i20", 3),
            ("Uneven front tire shoulder wear accompanied by metallic knocking over rough city streets", "car", "Honda", "City", 3),

            # CAR: Brake Pads (Part 4)
            ("High-pitched squealing and screeching noise whenever brake pedal is pressed", "car", "Hyundai", "i20", 4),
            ("Brake pedal feels spongy and soft, car takes noticeably longer distance to come to complete stop", "car", "Hyundai", "i20", 4),
            ("Grinding metallic sound when stopping, brake friction material completely worn down to backing plate", "car", "Maruti", "Swift", 4),
            ("Brake warning light illuminated on dashboard with screeching sound during light deceleration", "car", "Honda", "City", 4),

            # CAR: Brake Disc Rotor (Part 5)
            ("Severe pulsation and shaking felt through brake pedal and steering wheel when braking at highway speeds", "car", "Hyundai", "i20", 5),
            ("Deep grooves and scoring visible on brake rotor surface with loud grinding during heavy braking", "car", "Hyundai", "i20", 5),
            ("Front brakes shuddering violently under downhill deceleration, disc warped due to heat", "car", "Maruti", "Swift", 5),

            # CAR: Clutch Plate Kit (Part 6)
            ("Engine RPM revs up quickly but car accelerates very sluggishly especially uphill", "car", "Hyundai", "i20", 6),
            ("Burning smell inside cabin when climbing flyovers, clutch slipping severely under throttle", "car", "Hyundai", "i20", 6),
            ("Gears grinding and difficult to engage first gear or reverse with clutch pedal fully depressed", "car", "Maruti", "Swift", 6),

            # CAR: Battery (Part 7)
            ("Engine cranks very sluggishly or makes rapid clicking sound and refuses to start in the morning", "car", "Hyundai", "i20", 7),
            ("Completely dead ignition, no dashboard lights or horn working until jump-started", "car", "Hyundai", "i20", 7),
            ("Battery indicator light glowing red on cluster, car died immediately after headlights turned on", "car", "Maruti", "Swift", 7),

            # CAR: Alternator (Part 8)
            ("Battery warning light stays on while driving and headlights dim dramatically at idle", "car", "Hyundai", "i20", 8),
            ("Whining or growling noise from engine serpentine belt area and electrical accessories malfunctioning", "car", "Hyundai", "i20", 8),
            ("Car stalled while driving in traffic after battery drained completely, alternator not charging", "car", "Honda", "City", 8),

            # CAR: Spark Plugs (Part 9)
            ("Engine misfiring on cylinder 2, rough idling and jerking hesitation during rapid acceleration", "car", "Hyundai", "i20", 9),
            ("Noticeable drop in fuel economy with sputtering exhaust sound and sluggish throttle response", "car", "Hyundai", "i20", 9),
            ("Check engine light flashing with P0300 random misfire code, fouled plugs observed", "car", "Maruti", "Swift", 9),

            # CAR: Air Filter (Part 10)
            ("Sluggish throttle response, black smoke from tailpipe and reduced engine power output", "car", "Hyundai", "i20", 10),
            ("Engine struggling to breathe under load, dirty clogged air intake element inspected", "car", "Hyundai", "i20", 10),

            # CAR: Oil Filter (Part 11)
            ("Low oil pressure warning lamp flickering on dashboard at idle with dark dirty lubricant", "car", "Hyundai", "i20", 11),
            ("Routine oil change service maintenance replacement, oil filter housing clogged", "car", "Maruti", "Swift", 11),

            # CAR: Timing Chain Kit (Part 12)
            ("Rattling and slapping metallic chain sound from timing cover side on cold morning engine start", "car", "Hyundai", "i20", 12),
            ("Engine check light with camshaft crankshaft correlation error code P0016, timing jumped", "car", "Hyundai", "i20", 12),
            ("Severe rattling noise that quiets down slightly when engine warms up, slack timing chain", "car", "Maruti", "Swift", 12),

            # CAR: Headlight Bulb (Part 13)
            ("Front right low-beam headlight not illuminating, high-beam works normally", "car", "Hyundai", "i20", 13),
            ("Headlamp bulb filament broken after driving over rough bumpy terrain", "car", "Maruti", "Swift", 13),

            # CAR: Radiator Core (Part 14)
            ("Engine temperature gauge rising into red danger zone with green coolant puddle under front bumper", "car", "Hyundai", "i20", 14),
            ("Steam billowing from under radiator cap and sweet maple smell of boiling ethylene glycol", "car", "Hyundai", "i20", 14),
            ("Radiator plastic end tank cracked causing rapid loss of cooling fluid during commute", "car", "Honda", "City", 14),

            # CAR: Wiper Motor & Linkage (Part 15)
            ("Windshield wipers moving extremely slowly or completely stuck halfway across windshield in rain", "car", "Hyundai", "i20", 15),
            ("Wiper motor hums loudly under cowl but wiper arms do not sweep windshield", "car", "Hyundai", "i20", 15),

            # CAR: Tie Rod End (Part 16)
            ("Car pulls strongly to one side of road, excessive play and free play in steering wheel", "car", "Hyundai", "i20", 16),
            ("Front end alignment wandering constantly with noticeable clunk when wiggling front tire", "car", "Hyundai", "i20", 16),

            # CAR: Wheel Bearing Hub (Part 17)
            ("Continuous roaring or humming drone from front wheel that gets louder with vehicle speed", "car", "Hyundai", "i20", 17),
            ("Growling noise from wheel hub that changes pitch when swerving left or right", "car", "Hyundai", "i20", 17),

            # CAR: Water Pump (Part 18)
            ("Chirping noise from front serpentine pulley and coolant dripping from weep hole underneath", "car", "Hyundai", "i20", 18),
            ("Engine overheating rapidly while coolant reservoir is full, water pump impeller failure", "car", "Hyundai", "i20", 18),

            # CAR: Fuel Pump (Part 19)
            ("Car sputters and stalls at highway speeds like running out of gas despite full fuel tank", "car", "Hyundai", "i20", 19),
            ("High-pitched whining buzz from fuel tank underneath rear seat, engine cranks but gets no fuel", "car", "Hyundai", "i20", 19),

            # CAR: Ignition Coil (Part 20)
            ("Severe engine shaking and shuddering when stepping on gas pedal, flashing check engine code", "car", "Hyundai", "i20", 20),
            ("One cylinder dead, strong smell of unburnt fuel from tailpipe due to faulty coil pack", "car", "Hyundai", "i20", 20),

            # ======================== BIKE CASES ========================
            # BIKE: Drive Chain & Sprocket (Part 21)
            ("Drive chain making excessive clanking and slapping noise against swingarm during acceleration", "bike", "Royal Enfield", "Classic 350", 21),
            ("Motorcycle chain slipping and hopping over rear sprocket teeth under hard throttle uphill", "bike", "Royal Enfield", "Classic 350", 21),
            ("Rear sprocket teeth hooked and pointed sharp like shark fins, chain loose beyond tensioner adjustment", "bike", "Royal Enfield", "Classic 350", 21),
            ("Jerky power delivery and metallic slapping noise from motorcycle secondary drive system", "bike", "Bajaj", "Pulsar 150", 21),

            # BIKE: Motorcycle Clutch Friction Plates (Part 22)
            ("Clutch lever has zero resistance or feels spongy with gears extremely stiff and hard to shift", "bike", "Royal Enfield", "Classic 350", 22),
            ("Engine RPM revs up loudly when twisting motorcycle throttle but bike barely moves forward", "bike", "Royal Enfield", "Classic 350", 22),
            ("Motorcycle creeps forward violently when placed in first gear even with clutch lever fully pulled in", "bike", "Royal Enfield", "Classic 350", 22),
            ("Severe clutch slippage and burnt friction smell from motorcycle wet clutch casing", "bike", "TVS", "Apache RTR", 22),

            # BIKE: Throttle Cable (Part 23)
            ("Motorcycle accelerator twist grip feels stiff, sticky or snapped completely with no throttle response", "bike", "Royal Enfield", "Classic 350", 23),
            ("Twist throttle fails to snap back automatically to idle position when released", "bike", "Royal Enfield", "Classic 350", 23),
            ("Frayed steel throttle wire binding inside sleeve causing high engine idle revving", "bike", "Bajaj", "Pulsar 150", 23),

            # BIKE: Tail Light Assembly (Part 24)
            ("Rear tail light housing cracked and brake stop light not illuminating when lever is pulled", "bike", "Royal Enfield", "Classic 350", 24),
            ("Tail lamp red lens broken due to vibration, bulb exposed and water entering casing", "bike", "Royal Enfield", "Classic 350", 24),

            # BIKE: Brake Pads (Part 25)
            ("Loud metallic grinding from motorcycle front disc caliper when applying hand brake lever", "bike", "Royal Enfield", "Classic 350", 25),
            ("Motorcycle front brake lever feels spongy and stopping distance has doubled", "bike", "Royal Enfield", "Classic 350", 25),
            ("Brake squeal from Bybre disc caliper, friction pad lining worn below minimum wear indicator groove", "bike", "Bajaj", "Pulsar 150", 25),

            # BIKE: Battery (Part 26)
            ("Motorcycle self-start button produces rapid clicking relay sound and starter will not turn", "bike", "Royal Enfield", "Classic 350", 26),
            ("Bike only starts with kick lever, neutral light dims completely when horn is pressed", "bike", "Royal Enfield", "Classic 350", 26),
            ("12V bike battery voltage dropped to 10V, cannot hold charge overnight", "bike", "Honda", "Activa 6G", 26),

            # BIKE: Rear Shocks (Part 27)
            ("Rear motorcycle suspension bottoming out harshly with clunk over minor speed bumps", "bike", "Royal Enfield", "Classic 350", 27),
            ("Oil leaking down chrome body of rear shock absorber, bouncy un-damped rebound ride", "bike", "Royal Enfield", "Classic 350", 27),

            # BIKE: Spark Plug (Part 28)
            ("Motorcycle engine misfires intermittently, backfiring through exhaust with black carbon fouling", "bike", "Royal Enfield", "Classic 350", 28),
            ("Bike cuts off suddenly during rain or idle, weak yellowish spark produced at plug tip", "bike", "Bajaj", "Pulsar 150", 28),

            # BIKE: Fork Oil Seals (Part 29)
            ("Oil oozing past front fork stanchion tubes covering front disc brake in fluid", "bike", "Royal Enfield", "Classic 350", 29),
            ("Front forks diving excessively and clunking loudly on compression, cracked dust seals", "bike", "Royal Enfield", "Classic 350", 29),

            # BIKE: Fuel Injector (Part 30)
            ("BS6 motorcycle engine hesitates, surges violently at mid-range RPM and stumbles off idle", "bike", "Royal Enfield", "Classic 350", 30),
            ("Fuel injector nozzle clogged with varnish deposits causing lean misfire and hard starting", "bike", "Royal Enfield", "Classic 350", 30),
        ]

        print(f"[Seed] Computing Sentence-BERT embeddings for {len(cases_raw)} repair cases...")
        for i, (sym, vtype, make, model, pid) in enumerate(cases_raw, 1):
            emb_vec = encode_text(sym)  # 384-dim normalized float32
            emb_bytes = emb_vec.tobytes()

            rc = RepairCase(
                symptoms=sym,
                vehicle_type=vtype,
                make=make,
                model=model,
                solution_part_id=pid,
                embedding=emb_bytes,
            )
            db.add(rc)

            if i % 10 == 0 or i == len(cases_raw):
                print(f"  -> Encoded {i}/{len(cases_raw)} cases")

        db.commit()
        print(f"[Seed] Successfully seeded {len(cases_raw)} repair cases into SQLite!")
        print("[Seed] Seeding completed successfully.")

    except Exception as e:
        db.rollback()
        print(f"[Seed] Error during seeding: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
