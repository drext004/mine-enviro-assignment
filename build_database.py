import sqlite3
import json
import re
import os

DB_FILE = "mine_explosions.db"

def init_database():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 1. Historical Major Disasters (1901-2022)
    cursor.execute('''
    CREATE TABLE historical_disasters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sl_no INTEGER,
        date TEXT,
        year INTEGER,
        mine_name TEXT,
        coalfield_state TEXT,
        killed INTEGER,
        injured INTEGER,
        official_cause TEXT,
        disaster_type TEXT
    )
    ''')

    # 2. Recent Incidents (2016-2022 Detailed Cases)
    cursor.execute('''
    CREATE TABLE recent_incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_no INTEGER,
        date TEXT,
        year INTEGER,
        mine_name TEXT,
        company TEXT,
        district TEXT,
        state TEXT,
        place_code TEXT,
        place_desc TEXT,
        cause_code TEXT,
        cause_desc TEXT,
        root_cause_category TEXT,
        killed INTEGER,
        injured INTEGER,
        victim_details TEXT,
        cmr_violations TEXT,
        physical_mechanism TEXT,
        full_narrative TEXT
    )
    ''')

    # 3. Courts of Inquiry (1901-2022)
    cursor.execute('''
    CREATE TABLE courts_of_inquiry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inq_no INTEGER,
        date TEXT,
        year INTEGER,
        mine_name TEXT,
        cause TEXT,
        killed INTEGER,
        president TEXT,
        assessors TEXT
    )
    ''')

    # 4. Annual Statistics (2016-2022)
    cursor.execute('''
    CREATE TABLE annual_stats (
        year INTEGER PRIMARY KEY,
        dust_gas_fatal_acc INTEGER,
        dust_gas_fatalities INTEGER,
        dust_gas_serious_acc INTEGER,
        explosives_fatal_acc INTEGER,
        explosives_fatalities INTEGER,
        explosives_serious_inj INTEGER,
        explosives_serious_acc INTEGER
    )
    ''')

    # 5. Cause Taxonomy Aggregates
    cursor.execute('''
    CREATE TABLE cause_taxonomy (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT UNIQUE,
        fatal_incidents INTEGER,
        total_deaths INTEGER,
        key_mechanism TEXT,
        primary_regulations TEXT
    )
    ''')

    conn.commit()
    return conn

def populate_historical_disasters(conn):
    cursor = conn.cursor()
    
    historical_data = [
        (1, '31-10-1901', 1901, 'Tikkak', 'Assam', 4, 0, 'Explosions of damp/coal dust', 'Coal Dust'),
        (3, '01-04-1906', 1906, 'Upper Ledo', 'Assam', 4, 0, 'Suffocation by gases', 'Gas Suffocation'),
        (4, '16-06-1908', 1908, 'Nadir Khas', 'Punjab / Salt Range', 20, 0, 'Explosions of fire-damp', 'Firedamp'),
        (11, '07-02-1910', 1910, 'Dishergarh', 'Raniganj, West Bengal', 11, 0, 'Explosion of fire-damp', 'Firedamp'),
        (15, '26-11-1910', 1910, 'Namdang', 'Assam', 14, 4, 'Explosion of fire-damp', 'Firedamp'),
        (16, '09-11-1911', 1911, 'Kendwadih', 'Jharia, Jharkhand', 14, 0, 'Explosion of fire-damp', 'Firedamp'),
        (23, '22-10-1913', 1913, 'Chowrasi', 'Raniganj, West Bengal', 27, 0, 'Explosion of fire-damp', 'Firedamp'),
        (29, '20-07-1916', 1916, 'Dishergarh', 'Raniganj, West Bengal', 14, 4, 'Explosion of Fire-damp', 'Firedamp'),
        (31, '18-11-1918', 1918, 'Dishergarh', 'Raniganj, West Bengal', 10, 4, 'Explosion of Fire-damp', 'Firedamp'),
        (40, '20-02-1921', 1921, 'Barkui', 'Pench Valley, MP', 4, 1, 'Explosives', 'Explosives'),
        (41, '28-02-1921', 1921, 'Amlabad', 'Jharia, Jharkhand', 11, 0, 'Explosion or Fire-damp', 'Firedamp'),
        (44, '09-03-1922', 1922, 'Khost', 'Baluchistan', 13, 3, 'Explosions', 'Firedamp / Dust'),
        (46, '05-07-1922', 1922, 'Parbelia', 'Raniganj, West Bengal', 4, 2, 'Explosions', 'Firedamp / Dust'),
        (47, '04-01-1923', 1923, 'Parbelia', 'Raniganj, West Bengal', 74, 0, 'Explosion/Ignition of Firedamp', 'Firedamp / Dust'),
        (52, '01-05-1923', 1923, 'Sodepur', 'Raniganj, West Bengal', 9, 0, 'Suffocation of Gases', 'Gas Suffocation'),
        (57, '05-07-1924', 1924, 'Bararee', 'Jharia, Jharkhand', 4, 0, 'Explosives', 'Explosives'),
        (67, '16-04-1929', 1929, 'Sawang', 'Bokaro, Jharkhand', 6, 3, 'Explosion of Firedamp', 'Firedamp'),
        (72, '24-02-1930', 1930, 'Bararee', 'Jharia, Jharkhand', 4, 0, 'Suffocation by Gases', 'Gas Suffocation'),
        (74, '14-10-1930', 1930, 'Dishergarh West', 'Raniganj, West Bengal', 6, 0, 'Explosion of Firedamp', 'Firedamp'),
        (75, '17-02-1931', 1931, 'Nongah', 'Raniganj, West Bengal', 13, 3, 'Explosives', 'Explosives'),
        (77, '09-04-1932', 1932, 'Methani', 'Raniganj, West Bengal', 5, 2, 'Explosion/Ignition of Firedamp', 'Firedamp'),
        (82, '29-06-1935', 1935, 'Bagdigi', 'Jharia, Jharkhand', 19, 7, 'Explosion/Ignition of Firedamp', 'Firedamp / Dust'),
        (83, '24-07-1935', 1935, 'Kurhurbaree', 'Giridih, Jharkhand', 62, 14, 'Explosion/Ignition of Firedamp', 'Firedamp / Dust'),
        (84, '30-01-1936', 1936, 'Loyabad', 'Jharia, Jharkhand', 35, 0, 'Fire/Suffocation by Gases', 'Gas Suffocation / Fire'),
        (85, '14-07-1936', 1936, 'Adjai Second', 'Raniganj, West Bengal', 4, 1, 'Explosion/Ignition of Firedamp', 'Firedamp'),
        (87, '18-12-1936', 1936, 'Poidih', 'Raniganj, West Bengal', 209, 0, 'Explosion/Ignition of Firedamp', 'Firedamp & Coal Dust'),
        (91, '16-04-1940', 1940, 'Raneepur', 'Raniganj, West Bengal', 4, 1, 'Explosion/Ignition of Firedamp', 'Firedamp'),
        (95, '28-12-1940', 1940, 'Kustore', 'Jharia, Jharkhand', 4, 0, 'Suffocation by Gases', 'Gas Suffocation'),
        (107, '14-04-1943', 1943, 'Banksimulla 11 & 12 Pits', 'Raniganj, West Bengal', 5, 0, 'Explosions', 'Firedamp / Dust'),
        (108, '26-07-1943', 1943, 'Ghorawari', 'Chhindwara, MP', 7, 0, 'Explosions', 'Firedamp / Dust'),
        (117, '19-03-1946', 1946, 'Begunia', 'Raniganj, West Bengal', 13, 0, 'Explosion/Ignition of Firedamp', 'Firedamp'),
        (121, '23-03-1948', 1948, 'Chapui Khas', 'Raniganj, West Bengal', 5, 1, 'Explosions', 'Firedamp'),
        (153, '14-03-1954', 1954, 'Damra', 'Raniganj, West Bengal', 10, 0, 'Explosion/Ignition of Firedamp', 'Firedamp'),
        (159, '05-02-1955', 1955, 'Amlabad', 'Jharia, Jharkhand', 52, 1, 'Explosion of Inflamable Gas', 'Firedamp / Dust'),
        (168, '19-02-1958', 1958, 'Chinakuri 1 & 2 Pits', 'Raniganj, West Bengal', 176, 7, 'Explosions', 'Firedamp & Inundation'),
        (171, '27-01-1959', 1959, 'Saunda II', 'Karanpura, Jharkhand', 4, 0, 'Explosion of Inflamable Gas', 'Firedamp'),
        (191, '28-05-1965', 1965, 'Dhori', 'Bokaro, Jharkhand', 268, 9, 'Explosion of Coal Dust', 'Coal Dust (Worst in India)'),
        (204, '18-03-1973', 1973, 'Noonodih Jitpur', 'Jharia, Jharkhand', 48, 13, 'Explosion/Ignition of Gas/Dust', 'Firedamp & Coal Dust'),
        (209, '31-10-1974', 1974, 'Ranipur', 'Raniganj, West Bengal', 4, 1, 'Explosion/Ignition of Gas/Dust', 'Firedamp / Dust'),
        (222, '04-10-1976', 1976, 'Sudamdih Shaft', 'Jharia, Jharkhand', 43, 3, 'Explosion/Ignition of Gas/Dust', 'Firedamp & Coal Dust'),
        (226, '22-01-1979', 1979, 'Baragolai', 'Assam', 16, 0, 'Explosion/Ignition of Gas/Dust', 'Firedamp & Coal Dust'),
        (234, '18-09-1984', 1984, 'Saunda D West', 'Karanpura, Jharkhand', 6, 0, 'Explosives', 'Explosives'),
        (238, '27-03-1986', 1986, 'Godavari Khani No. 9', 'Godavari Valley, Telangana', 7, 0, 'Explosion/Ignition of Gas/Dust', 'Firedamp & Coal Dust'),
        (247, '19-11-1993', 1993, 'Tipong', 'Assam', 9, 0, 'Explosion/Ignition of Gas/Dust', 'Firedamp & Coal Dust'),
        (256, '03-03-1997', 1997, 'New Moghla', 'Jammu & Kashmir', 10, 12, 'Explosion/Ignition of Gas/Dust', 'Firedamp & Coal Dust'),
        (272, '06-09-2006', 2006, 'Bhatdee', 'Jharia, Jharkhand', 50, 0, 'Explosion/Ignition of Gas/Dust', 'Firedamp & Coal Dust'),
        (275, '11-05-2008', 2008, 'Ledo', 'Assam', 5, 14, 'Explosion/Ignition of Gas/Dust', 'Firedamp & Coal Dust'),
        (277, '06-05-2010', 2010, 'Anjan Hill', 'Chirimiri, Chhattisgarh', 15, 5, 'Other explosive accident / Ignition of Gas/Dust', 'Goaf Fire -> Firedamp Explosion')
    ]

    cursor.executemany('''
    INSERT INTO historical_disasters (sl_no, date, year, mine_name, coalfield_state, killed, injured, official_cause, disaster_type)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', historical_data)
    conn.commit()
    print(f"Inserted {len(historical_data)} historical disasters.")

def populate_recent_incidents(conn):
    cursor = conn.cursor()

    recent_cases = [
        (
            1, 56, '12.03.16', 2016, 'CHHATARPUR MINE NO.I', 'WCL', 'Betul', 'Madhya Pradesh',
            '111', 'Belowground Development Area (< 10m of face)',
            '0774', 'Explosion/Ignition of Gas/Dust etc.',
            'Solid Blasting Igniting Methane in Blind Heading',
            1, 0,
            'Prakash Bihare, Blasting crewman, Male, 40 Years (Fatal, died after 42 hrs from burns)',
            'CMR 1957 Reg 175(2), Reg 168(15), Reg 113(3)(b), Reg 143, Reg 130(1), 146(1), 136A',
            'Development face blasted within 2.5m of an opposite gallery; solid blast ignited inflammable gas accumulated in the blind heading due to air velocity < 30 m/min and extension > 4.5m without brattice.',
            'While development face lying within 2.5m of an opposite gallery was blasted in an underground coal mine, it ignited the inflammable gas accumulated therein the opposite gallery, inflicting serious burn injuries to a blasting crewman posted as guard, who died in the hospital after about forty two hours during treatment.'
        ),
        (
            2, 34, '24.06.20', 2020, 'KURASIA COLLIERY', 'SECL', 'Korea', 'Chhattisgarh',
            '131', 'Belowground Depillaring Panel Split Face (< 10m)',
            '0555', 'Misfires/Sockets(While Drilling into)',
            'Drilling into Misfired Shot Hole (Accidental Detonation)',
            1, 0,
            'Dhaneshwar, Helper, Male, 58 Years (Fatal, multiple projectile injuries)',
            'CMR 2017 Reg 49(f), Reg 203(1), Reg 206(2), Reg 48(1), Reg 129(5), Reg 33(1)',
            'UDM operator drilled into a misfired shothole of the previous shift; explosive charge detonated, projecting shrapnel at helper.',
            'While a UDM operator was drilling holes with UDM at the floor near a split face of depillaring panel in an underground mine, the drill rod of the UDM accidentally holed into a misfired shot of previous shift causing it to explode, in which an UDM helper was hit by blast projectiles.'
        ),
        (
            3, 35, '02.09.20', 2020, 'RAVINDRA KHANI NO.5', 'SCCL', 'Adilabad', 'Telangana',
            '111', 'Belowground Split Gallery (< 10m)',
            '0555', 'Misfires/Sockets(While Drilling into)',
            'Drilling into Misfired Shot Hole (Accidental Detonation)',
            1, 3,
            'R. Lingaiah, Cutter, Male, 54 Years (Fatal); 3 crew members seriously injured',
            'CMR 2017 Reg 203, Reg 204, Reg 129(5), Reg 110',
            'Drill bit contacted undetonated explosive charge in a misfired hole in split gallery, triggering instantaneous explosion.',
            'While a crew of five persons engaged in drilling operation at a split gallery of an underground coal mine, suddenly the drill bit came in contact with explosive charge of a shot hole (misfire) and got blasted; inflicting fatal injuries to one crew member and serious injuries to three others.'
        ),
        (
            4, 33, '02.06.20', 2020, 'RAMAGUNDAM OC-I', 'SCCL', 'Peddapalli', 'Telangana',
            '222', 'Opencast Quarry Bed / Secondary Blasting Area',
            '0553', 'Secondary Blasting Projectiles',
            'Deep Hole / Secondary Blasting Operational Failure',
            4, 3,
            '4 Workers Killed on spot/way to hospital, 3 Seriously Injured (Major Disaster)',
            'CMR 2017 Reg 104(1)(2)(3), Reg 104(5)(e), Reg 104(8), Reg 239; MVTR 1966 Rule 13',
            'Crew charged large diameter holes drilled in big boulders (2x3x3m) with bulk Site Mixed Emulsion (SME) explosive; column exploded violently during charging.',
            'While a group of seven persons were charging explosive in large diameter holes, drilled in big boulders for secondary blasting in an opencast coal mine, suddenly the explosive column, poured in hole, exploded inflicting fatal injuries to four and serious injuries to three.'
        ),
        (
            5, 35, '12.09.19', 2019, 'AMALGAMATED KESHALPUR-WEST MUDIDIH', 'BCCL', 'Dhanbad', 'Jharkhand',
            '213', 'Opencast Overburden Bench',
            '0552', 'Deep Hole Blasting Projectiles',
            'Deep Hole / Secondary Blasting Operational Failure',
            1, 3,
            'D.D. Mahto, Exp. Carrier, Male, 38 Years (Fatal); Overman and 2 others seriously injured',
            'CMR 2017 Reg 195(8)(c)&(d), Reg 196(2)(b), Reg 195(7)(c)',
            'Two contiguous OB benches charged with SME and detonating cord; lower patch initiated without evacuating upper patch due to miscommunication, causing simultaneous detonation.',
            'While charging of deep holes with SME explosive and detonating cord was being carried out in an OB bench immediately above another charged bench, the lower patch was initiated for blasting without ensuring withdrawal of persons at upper patch, causing explosion in both patches.'
        ),
        (
            6, 35, '02.02.18', 2018, 'MANIKPUR OCP', 'SECL', 'Korba', 'Chhattisgarh',
            '213', 'Opencast Overburden Bench',
            '0555', 'Misfires/Sockets(While Drilling into)',
            'Drilling into Misfired Shot Hole (Accidental Detonation)',
            1, 0,
            'R.K. Kushre, Drill Helper, Male, 18 Years (Fatal)',
            'CMR 2017 Reg 204, Reg 239',
            'Drill bit struck an undetected misfire shot on OB bench; explosion blew a 1.2x1.2x0.5m crater and hurled shrapnel/ejected drill machine parts at helper.',
            'While drilling was being carried out on an overburden bench in night shift, the rotating drill bit hit a misfire shot of earlier blasting, which exploded, creating a crater and fatally striking the drill helper.'
        ),
        (
            7, 34, '23.11.18', 2018, 'KULDA OPENCAST MINE', 'MCL', 'Sundergarh', 'Odisha',
            '231', 'Opencast Haul Road / Coal Bench Danger Zone',
            '0552', 'Deep Hole Blasting Projectiles',
            'Deep Hole / Secondary Blasting Operational Failure',
            1, 0,
            'Md. Israfil Ansari, Tipper Operator, Male, 24 Years (Fatal)',
            'CMR 2017 Reg 196(2)(b), Reg 194; GSR 985(E)',
            'Tipper entered within the 500m danger zone during bench blasting; blast shockwave and mass displacement overturned tipper.',
            'While a coal bench was blasted, a tipper entered within the danger zone and was overturned due to effect of blasting inflicting fatal bodily injuries to the operator.'
        ),
        (
            8, 29, '28.08.21', 2021, 'BOKARO', 'CCL', 'Bokaro', 'Jharkhand',
            '231', 'Opencast Haul Road (170m from face)',
            '0552', 'Deep Hole Blasting Projectiles',
            'Deep Hole / Secondary Blasting Operational Failure',
            1, 0,
            'T. Khan, Driver, Male, 49 Years (Fatal)',
            'CMR 2017 Reg 196, Reg 194',
            'Flyrock projectile travelled 170m from blasting face and penetrated cabin of explosive transport van parked on haul road.',
            'While a driver was sitting in the cabin of an explosive van parked 170m away from the blasting face with door partially open, flyrock projectile from deep hole blasting pierced vehicle.'
        ),
        (
            9, 57, '10.04.16', 2016, 'MIC JHANJHRA PROJECT', 'ECL', 'Burdwan', 'West Bengal',
            '322', 'Surface Workshop / Scrap Yard',
            '0778', 'Other Combustible Material',
            'Surface Gas / Cylinder Explosion',
            2, 0,
            '1. P.S. Ghosh, 43 Yrs; 2. M. Kanakaiah, 61 Yrs (Contract workers, fatal burns)',
            'Factories Act & Safe Standard Operating Procedures for Hot Work',
            'Gas cutting torch flame applied to closed metallic unpurged hydraulic oil drum; internal hydrocarbon vapors exploded violently.',
            'While a welder was cutting a closed metallic empty hydraulic oil drum with his helper by gas cutting on surface, the accumulated gas inside drum exploded resulting in fatal burn injuries to both.'
        ),
        (
            10, 41, '05.05.18', 2018, 'DUDHICHUA PROJECT', 'NCL', 'Singrauli', 'Madhya Pradesh',
            '222', 'Surface Depot / Coal Heap Edge',
            '0779', 'Other Accidents due to Dust/Gas/Fire',
            'Surface Gas / Cylinder Explosion',
            1, 0,
            'L. Gupta, Mechanical Fitter, Male, 59 Years (Fatal)',
            'CMR 2017 Reg 239, Reg 210(1)',
            'Reversing dozer ran over and crushed an unshielded oxygen cylinder kept near coal heap, initiating sudden mechanical rupture and explosive fire.',
            'While reversing, a dozer rolled over an oxygen cylinder kept on surface near coal heap and caused explosion inflicting serious burn injuries to a fitter in vicinity.'
        ),
        (
            11, 42, '16.12.18', 2018, 'BAGDEWA U/G MINE', 'SECL', 'Korba', 'Chhattisgarh',
            '111', 'Belowground Development Connection to Sealed Area',
            '0779', 'Other Accidents due to Dust/Gas/Fire',
            'Inadequate Ventilation Leading to Irrespirable Atmosphere',
            3, 0,
            '1. Laxmikant Prasad (Sirdar, 41); 2. Ramadhar Yadav (Crew, 33); 3. Ajay Kumar (Mazdoor, 34)',
            'CMR 2017 Reg 153, Reg 239, Reg 112, Reg 142',
            'Drilling and blasting holed through into adjacent sealed-off unventilated district; toxic/asphyxiating blackdamp rushed in; 3 collapsed and died in sequence.',
            'While two persons entered inbye of a development connection to an adjacent sealed-off area made by blasting, they were asphyxiated by irrespirable atmosphere; a rescuer also collapsed and died.'
        ),
        (
            12, 55, '19.07.16', 2016, 'GODAVARI KHANI NO.7(LE)PROJECT', 'SCCL', 'Karimnagar', 'Telangana',
            '141', 'Belowground Discontinued Blind Gallery',
            '0771', 'Occurrence of Gas',
            'Inadequate Ventilation Leading to Irrespirable Atmosphere',
            1, 0,
            'Minganaboina Anil, BG worker, Male, 22 Years (Fatal)',
            'CMR 1957 Reg 43(3)(b), Reg 43(6), Reg 42(1), Reg 130',
            'Worker walked into unventilated blind gallery having blackdamp accumulation for attending nature call; instantaneous collapse from hypoxia.',
            'While a worker entered in an irrespirable atmosphere of an underground coal mine for attending nature call, collapsed and succumbed almost instantaneously.'
        ),
        (
            13, 50, '18.07.19', 2019, 'KUMBHARKHANI U/G', 'WCL', 'Yavatmal', 'Maharashtra',
            '180', 'Incline of Discontinued Mine',
            '0771', 'Occurrence of Gas',
            'Inadequate Ventilation Leading to Irrespirable Atmosphere',
            2, 0,
            '1. G.K. Rameshwaram (35); 2. R.K. Singh (30)',
            'CMR 2017 Reg 73(2), Reg 237(1), Reg 137(15), Reg 142(4)',
            'Two persons bypassed partial fencing at entrance of discontinued incline; suffocated due to oxygen deficiency and blackdamp accumulation.',
            'While two persons entered inside the incline of a discontinued mine, crossing partial fencing, they were found dead due to asphyxia.'
        ),
        (
            14, 48, '07.04.20', 2020, 'GODAVARI KHANI NO.11 INCLINE MINE', 'SCCL', 'Karimnagar', 'Telangana',
            '199', 'Disused Belowground Workings',
            '0771', 'Occurrence of Gas',
            'Inadequate Ventilation Leading to Irrespirable Atmosphere',
            1, 0,
            'K. Sanjeev, Mazdoor, Male, 57 Years (Fatal, body found after 10 days)',
            'Mines Act Sec 72(b); CMR 2017 Reg 40(5), Reg 40(6), Reg 239',
            'Pump operator wandered into unventilated, abandoned workings and succumbed to blackdamp asphyxiation.',
            'While employed as pump operator in an underground coal mine, worker left his working place and travelled to disused workings, succumbing to irrespirable environment.'
        ),
        (
            15, 42, '01.03.21', 2021, 'CHORA 7 & 9 PIT COLLIERY', 'ECL', 'Burdwan', 'West Bengal',
            '141', 'Sectionalisation Stopping Roadway',
            '0771', 'Occurrence of Gas',
            'Inadequate Ventilation Leading to Irrespirable Atmosphere',
            1, 0,
            'Arup Mondal, Sampling Assistant, Male, 45 Years (Fatal)',
            'CMR 2017 Reg 142, Reg 153',
            'Gas leaked through sectionalisation isolation stopping; sampling assistant inhaling toxic/asphyxiating leakage suffered fatal distress.',
            'While a crew of three went for sampling at sectionalisation stopping, victim approached stopping where noxious gas had accumulated and succumbed.'
        ),
        (
            16, 24, '07.05.22', 2022, 'BARTARAI', 'SECL', 'Anuppur', 'Madhya Pradesh',
            '322', 'Surface Lamp Room / Servicing Table',
            '0999', 'Unclassified (Safety Lamp Ignition)',
            'Flame Safety Lamp Servicing Ignition Hazard',
            1, 0,
            'Ramkali, Lamp Fitter, Female, 56 Years (Fatal burns after 12 days)',
            'CMR 2017 Reg 40(4)(a), Reg 239, Reg 179(7)',
            'Igniting flame safety lamp on same bench as cleaning/fuel refilling; burning match ignited fuel-soaked wiping cloth and clothing.',
            'While a female lamp fitter was igniting a flame safety lamp, burning match stick dropped on a wiping cloth partially soaked with fuel, causing fatal burn injuries.'
        ),
        (
            17, 17, '24.06.22', 2022, 'SELECTED DHORI QRY.NO.1 (KALYANI PROJ.)', 'CCL', 'Bokaro', 'Jharkhand',
            '214', 'Opencast Coal Bench / Burning Rib',
            '0779', 'Other Accidents due to Dust/Gas/Fire',
            'Spontaneous Combustion & Active Coal Fires',
            1, 0,
            'Mahendra Yadav, Cont. Employee (Excavator Operator), Male, 32 Years',
            'CMR 2017 Reg 239, Reg 110(4), Reg 106(4), Reg 108(2), Reg 138(1)&(2)',
            'Excavator deployed at toe of 11m high 72-degree bench having active spontaneous combustion fire; glowing red-hot coal chunk rolled into cabin.',
            'While excavator was deployed for loading OB from an old dump having fire in remnant coal rib, heated material rolled down and broke into cabin, inflicting fatal burn injuries.'
        ),
        (
            18, 18, '27.11.22', 2022, 'DIPKA MINE NO.IA', 'SECL', 'Korba', 'Chhattisgarh',
            '214', 'Opencast Ramp Bench near Fire Area',
            '0779', 'Other Accidents due to Dust/Gas/Fire',
            'Spontaneous Combustion & Active Coal Fires',
            1, 0,
            'Paras Ram Yadav, Contractor worker, Male, 35 Years (Fatal)',
            'CMR 2017 Reg 110(4), Reg 138',
            'Worker handling water hose on ramp bench slipped into burning coal ash and succumbed to extensive burn trauma.',
            'While contractor worker was trying to bring water hose pipe to bottom bench, slipped and fell on hot ash at bottom of ramp on fire.'
        ),
        (
            19, 58, '22.02.16', 2016, 'SALANPUR', 'BCCL', 'Dhanbad', 'Jharkhand',
            '214', 'Opencast Blasted Bench Berm',
            '0779', 'Other Accidents due to Dust/Gas/Fire',
            'Spontaneous Combustion & Active Coal Fires',
            1, 0,
            'Chandradeo Nonia, Dozer Operator, Male, 47 Years (Fatal)',
            'CMR 1957 Reg 42(3), Reg 190, Reg 50(a), Reg 36(1)(b); DGMS Circular 10/2004',
            'Dozer marched in reverse after blasting ran over berm and toppled; caught fire causing instantaneous fatal burns to operator.',
            'While a dozer not in safe working order was being marched in reverse after blasting, track chain ran over berm, causing toppling and fatal fire.'
        )
    ]

    cursor.executemany('''
    INSERT INTO recent_incidents (
        id, case_no, date, year, mine_name, company, district, state,
        place_code, place_desc, cause_code, cause_desc, root_cause_category,
        killed, injured, victim_details, cmr_violations, physical_mechanism, full_narrative
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', recent_cases)
    conn.commit()
    print(f"Inserted {len(recent_cases)} recent detailed cases.")

def populate_courts_of_inquiry(conn):
    cursor = conn.cursor()

    inquiry_data = [
        (3, '22/10/13', 1913, 'Chowrasi', 'Explosion', 27, 'Information not readily available', 'Information not readily available'),
        (6, '20/07/16', 1916, 'Dishergarh', 'Explosion', 14, 'Collector of Burdwan', '1. Chief Inspector of Mines; 2. G.C. Lathbury, Mining Engr.'),
        (7, '18/11/18', 1918, 'Dishergarh', 'Explosion', 10, 'Collector of Burdwan', '1. Chief Inspector of Mines; 2. T.H. Ward, Mining Engineer'),
        (9, '04/01/23', 1923, 'Parbelia', 'Explosion', 74, 'Deputy Commissioner', '1. Chief Inspector of Mines; 2. Colliery Superintendent'),
        (15, '14/10/30', 1930, 'Dishergarh West', 'Explosion', 6, 'Chief Inspector of Mines', '1. Dr. D. Penman, Mining Engr.; 2. J. Thomas, Mining Engr.'),
        (16, '29/06/35', 1935, 'Bagdigi', 'Explosion', 19, 'Chief Inspector of Mines', '1. Addl. Deputy Commissioner; 2. J.B. Wardlaw, Mining Engr.'),
        (17, '24/07/35', 1935, 'Kurhurbaree', 'Explosion', 62, 'Chief Inspector of Mines', '1. Deputy Commissioner; 2. J. Mackie, Mining Engineer'),
        (18, '30/01/36', 1936, 'Loyabad', 'Suffocation by Gases', 35, 'Commissioner, Chotanagpur', '1. Inspector of Mines; 2. J. Mackie, Mining Engr.; 3. B.K. Bose, Mining Engr.'),
        (19, '18/12/36', 1936, 'Poidih', 'Explosion', 209, 'Commissioner, Burdwan Division', '1. Inspector of Mines; 2. L.A. Jacobs, Mining Engr.; 3. B.K. Bose, Mining Engr.'),
        (20, '19/03/46', 1946, 'Begunia', 'Explosion', 13, 'Commissioner, Burdwan Division', '1. Dy. Chief Insp. of Mines; 2. J.K. Dholakia, Mining Engr.; 3. A.G. Mackay, Mining Engr.'),
        (24, '05/02/55', 1955, 'Amlabad', 'Explosion', 52, 'Justice B.P. Jamuar', '1. M.L. Shome, Mining Engr.; 2. N. Das, M.P.'),
        (26, '19/02/58', 1958, 'Chinakuri 1 & 2 Pits', 'Explosion', 176, 'Justice S.N. Guha Roy', '1. S.C. Samanta, M.P.; 2. Dr. J.W. Whitaker (Director CMRS)'),
        (28, '28/05/65', 1965, 'Dhori', 'Explosion', 268, 'Justice S.K. Das', '1. B.H. Engineer; 2. Das Gupta, G.S.I.'),
        (29, '18/03/73', 1973, 'Noonodih Jitpur', 'Explosion', 48, 'R.C. Dutt, I.C.S.', '1. Kanti Mehta; 2. Lalit Burman; 3. Prof. G.B. Mishra; 4. M.B. Tawadey'),
        (35, '04/10/76', 1976, 'Sudamdih Shaft', 'Explosion', 43, 'H.C. Sarin, I.C.S.', '1. S. Bagchi; 2. Damodar Pandey, M.P.'),
        (36, '22/01/79', 1979, 'Baragolai', 'Explosion', 16, 'T.S. Sankaran', '1. S. Dasgupta; 2. H.B. Ghose'),
        (41, '25/01/94', 1994, 'New Kenda', 'Ignition of Gas/Dust', 55, 'Justice S. Ahmed', '1. B.N. Tiwary, AITUC; 2. Prof. D.P. Singh, BHU-IT'),
        (47, '06/09/06', 2006, 'Bhatdee', 'Ignition of Gas/Dust', 50, 'P.C. Parakh', '1. Ravindra Sharma; 2. O.P. Lala'),
        (48, '06/05/10', 2010, 'Anjan Hill', 'Ignition of Gas/Dust', 15, 'Justice P.V. Shetty', '1. S.K. Dubey; 2. S. Kumar')
    ]

    cursor.executemany('''
    INSERT INTO courts_of_inquiry (inq_no, date, year, mine_name, cause, killed, president, assessors)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', inquiry_data)
    conn.commit()
    print(f"Inserted {len(inquiry_data)} Courts of Inquiry.")

def populate_annual_and_taxonomy(conn):
    cursor = conn.cursor()

    annual_data = [
        (2016, 4, 5, 0, 0, 0, 0, 1),
        (2017, 0, 0, 0, 0, 0, 0, 1),
        (2018, 2, 4, 0, 2, 2, 0, 2),
        (2019, 0, 0, 0, 1, 1, 3, 2),
        (2020, 0, 0, 0, 3, 6, 6, 1),
        (2021, 0, 0, 0, 2, 2, 0, 1),
        (2022, 2, 2, 1, 1, 1, 0, 1)
    ]

    cursor.executemany('''
    INSERT INTO annual_stats VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', annual_data)

    taxonomy_data = [
        ('Inadequate Ventilation Leading to Irrespirable Atmosphere', 5, 8,
         'Discontinued blind headings, unsealed goaves, and blackdamp (O2 < 19%, CO2/CO) accumulation without air coursing (air velocity < 30 m/min).',
         'CMR 1957 Reg 42, 43, 130; CMR 2017 Reg 153, 137, 142'),
        ('Deep Hole / Secondary Blasting Operational Failure', 4, 7,
         'Bulk SME explosive in large diameter boulder holes, dual-bench simultaneous detonation without clearing upper bench, and danger zone radius breaches.',
         'CMR 2017 Reg 104, 194, 195, 196, 239; MVTR 1966 Rule 13'),
        ('Drilling into Misfired Shot Holes (Accidental Detonation)', 3, 3,
         'Drill bit of UDM or rotary blast drill contacting undetonated explosive charge in sockets/misfired holes from preceding shifts.',
         'CMR 2017 Reg 203, 204, 206, 129(5), 49(f)'),
        ('Spontaneous Combustion & Active Coal Fires', 3, 3,
         'Heavy earthmoving machinery deployed at toe of benches containing burning remnant coal ribs; glowing coal lumps rolling into cabin.',
         'CMR 2017 Reg 106(4), 108(2), 110(4), 138, 239'),
        ('Surface Gas / Cylinder Explosion', 2, 3,
         'Gas cutting of unpurged hydraulic oil drums (vapor explosion); dozer crushing compressed oxygen cylinders.',
         'CMR 2017 Reg 210(1), 239; Factories Act Hot Work Rules'),
        ('Solid Blasting Igniting Methane in Blind Heading', 1, 1,
         'Solid blasting in development face within 2.5m of blind gallery; blown through shot ignited accumulated firedamp pocket.',
         'CMR 1957 Reg 175(2), 168(15), 113(3)(b), 143, 130, 136A')
    ]

    cursor.executemany('''
    INSERT INTO cause_taxonomy (category, fatal_incidents, total_deaths, key_mechanism, primary_regulations)
    VALUES (?, ?, ?, ?, ?)
    ''', taxonomy_data)

    conn.commit()
    print("Inserted Annual Stats and Root Cause Taxonomy.")

if __name__ == '__main__':
    conn = init_database()
    populate_historical_disasters(conn)
    populate_recent_incidents(conn)
    populate_courts_of_inquiry(conn)
    populate_annual_and_taxonomy(conn)
    conn.close()
    print(f"Database {DB_FILE} built successfully!")
