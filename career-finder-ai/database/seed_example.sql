-- seed_example.sql – Example seed data for local development
-- Run AFTER schema.sql:
--   sqlite3 database/career_finder.db < database/schema.sql
--   sqlite3 database/career_finder.db < database/seed_example.sql

-- ---------------------------------------------------------------------------
-- Companies
-- ---------------------------------------------------------------------------
INSERT OR IGNORE INTO companies (name, website, city, sector, size, verified) VALUES
    ('Saudi Aramco',       'https://www.aramco.com',         'Dhahran', 'Energy',         'Large',   1),
    ('STC',                'https://www.stc.com.sa',         'Riyadh',  'Telecom',        'Large',   1),
    ('Elm Company',        'https://www.elm.sa',             'Riyadh',  'Technology',     'Large',   1),
    ('KPMG Saudi Arabia',  'https://home.kpmg/sa',           'Jeddah',  'Consulting',     'Large',   1),
    ('Thiqah',             'https://www.thiqah.sa',          'Riyadh',  'Business Svcs',  'Medium',  1),
    ('Madar',              'https://www.madar.com',          'Dammam',  'Technology',     'Medium',  0),
    ('Siemens Saudi Arabia','https://www.siemens.com/sa',    'Jeddah',  'Engineering',    'Large',   1);

-- ---------------------------------------------------------------------------
-- Opportunities
-- ---------------------------------------------------------------------------
INSERT OR IGNORE INTO opportunities
    (company_id, title, city, work_mode, program_type, major_fit, duration_weeks, source_url)
VALUES
    (1, 'Data Science COOP',           'Dhahran', 'On-site', 'COOP',       'DS,CS,AI,DE', 24, 'https://www.aramco.com/careers'),
    (2, 'Cybersecurity Internship',    'Riyadh',  'Hybrid',  'Internship', 'CYS,CS,CE',   12, 'https://www.stc.com.sa/careers'),
    (3, 'Artificial Intelligence COOP','Riyadh',  'On-site', 'COOP',       'AI,CS,DS',    24, 'https://www.elm.sa/careers'),
    (4, 'FinTech Internship',          'Jeddah',  'Hybrid',  'Internship', 'FT,CIS,CS',   16, 'https://home.kpmg/sa/careers'),
    (5, 'Software Engineering COOP',   'Riyadh',  'Remote',  'COOP',       'CS,CE,CIS',   24, 'https://www.thiqah.sa/careers'),
    (6, 'Data Engineering Internship', 'Dammam',  'On-site', 'Internship', 'DE,DS,CS',    12, 'https://www.madar.com/careers'),
    (7, 'Computer Engineering COOP',   'Jeddah',  'On-site', 'COOP',       'CE,CS',       24, 'https://www.siemens.com/sa/careers');
