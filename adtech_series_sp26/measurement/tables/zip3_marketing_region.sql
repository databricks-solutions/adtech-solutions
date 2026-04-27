-- Table: zip3_marketing_region
-- Feature: AdTech Series Measurement Demo
--
-- Purpose: Lookup table mapping 3-digit ZIP prefixes to named US advertising markets.
--          JOIN'd directly in the pipeline on SUBSTRING(user_zip, 1, 3) = zip3.
--          Update rows here to remap regions — no pipeline redeploy needed.
--
-- Deploy: databricks sql execute --warehouse-id <warehouse_id> \
--           --file tables/zip3_marketing_region.sql --profile <profile>

CREATE OR REPLACE TABLE media_advertising.gold.zip3_marketing_region (
  zip3             STRING  NOT NULL COMMENT 'Three-digit ZIP prefix (000–999)',
  marketing_region STRING  NOT NULL COMMENT 'Named US advertising market'
)
USING DELTA
COMMENT 'Lookup table mapping ZIP3 prefixes to US advertising markets. \
JOIN'd directly in the pipeline on SUBSTRING(user_zip, 1, 3) = zip3. \
Update rows here to remap regions — no pipeline redeploy needed.';

INSERT OVERWRITE media_advertising.gold.zip3_marketing_region VALUES
  -- Puerto Rico: 006-009
  ('006','Puerto Rico'), ('007','Puerto Rico'), ('008','Puerto Rico'), ('009','Puerto Rico'),
  -- Western New England: 010-017
  ('010','Western New England'), ('011','Western New England'), ('012','Western New England'), ('013','Western New England'), ('014','Western New England'), ('015','Western New England'), ('016','Western New England'), ('017','Western New England'),
  -- Eastern Massachusetts: 018-019
  ('018','Eastern Massachusetts'), ('019','Eastern Massachusetts'),
  -- Boston Metro: 020-029
  ('020','Boston Metro'), ('021','Boston Metro'), ('022','Boston Metro'), ('023','Boston Metro'), ('024','Boston Metro'), ('025','Boston Metro'), ('026','Boston Metro'), ('027','Boston Metro'), ('028','Boston Metro'), ('029','Boston Metro'),
  -- New Hampshire: 030-038
  ('030','New Hampshire'), ('031','New Hampshire'), ('032','New Hampshire'), ('033','New Hampshire'), ('034','New Hampshire'), ('035','New Hampshire'), ('036','New Hampshire'), ('037','New Hampshire'), ('038','New Hampshire'),
  -- Maine: 039-049
  ('039','Maine'), ('040','Maine'), ('041','Maine'), ('042','Maine'), ('043','Maine'), ('044','Maine'), ('045','Maine'), ('046','Maine'), ('047','Maine'), ('048','Maine'), ('049','Maine'),
  -- Vermont: 050-059
  ('050','Vermont'), ('051','Vermont'), ('052','Vermont'), ('053','Vermont'), ('054','Vermont'), ('055','Vermont'), ('056','Vermont'), ('057','Vermont'), ('058','Vermont'), ('059','Vermont'),
  -- Connecticut: 060-069
  ('060','Connecticut'), ('061','Connecticut'), ('062','Connecticut'), ('063','Connecticut'), ('064','Connecticut'), ('065','Connecticut'), ('066','Connecticut'), ('067','Connecticut'), ('068','Connecticut'), ('069','Connecticut'),
  -- New Jersey Metro: 070-089
  ('070','New Jersey Metro'), ('071','New Jersey Metro'), ('072','New Jersey Metro'), ('073','New Jersey Metro'), ('074','New Jersey Metro'), ('075','New Jersey Metro'), ('076','New Jersey Metro'), ('077','New Jersey Metro'), ('078','New Jersey Metro'), ('079','New Jersey Metro'), ('080','New Jersey Metro'), ('081','New Jersey Metro'), ('082','New Jersey Metro'), ('083','New Jersey Metro'), ('084','New Jersey Metro'), ('085','New Jersey Metro'), ('086','New Jersey Metro'), ('087','New Jersey Metro'), ('088','New Jersey Metro'), ('089','New Jersey Metro'),
  -- APO/FPO: 090-099
  ('090','APO/FPO'), ('091','APO/FPO'), ('092','APO/FPO'), ('093','APO/FPO'), ('094','APO/FPO'), ('095','APO/FPO'), ('096','APO/FPO'), ('097','APO/FPO'), ('098','APO/FPO'), ('099','APO/FPO'),
  -- New York City Metro: 100-104
  ('100','New York City Metro'), ('101','New York City Metro'), ('102','New York City Metro'), ('103','New York City Metro'), ('104','New York City Metro'),
  -- Hudson Valley: 105-119
  ('105','Hudson Valley'), ('106','Hudson Valley'), ('107','Hudson Valley'), ('108','Hudson Valley'), ('109','Hudson Valley'), ('110','Hudson Valley'), ('111','Hudson Valley'), ('112','Hudson Valley'), ('113','Hudson Valley'), ('114','Hudson Valley'), ('115','Hudson Valley'), ('116','Hudson Valley'), ('117','Hudson Valley'), ('118','Hudson Valley'), ('119','Hudson Valley'),
  -- Upstate New York: 120-149
  ('120','Upstate New York'), ('121','Upstate New York'), ('122','Upstate New York'), ('123','Upstate New York'), ('124','Upstate New York'), ('125','Upstate New York'), ('126','Upstate New York'), ('127','Upstate New York'), ('128','Upstate New York'), ('129','Upstate New York'), ('130','Upstate New York'), ('131','Upstate New York'), ('132','Upstate New York'), ('133','Upstate New York'), ('134','Upstate New York'), ('135','Upstate New York'), ('136','Upstate New York'), ('137','Upstate New York'), ('138','Upstate New York'), ('139','Upstate New York'), ('140','Upstate New York'), ('141','Upstate New York'), ('142','Upstate New York'), ('143','Upstate New York'), ('144','Upstate New York'), ('145','Upstate New York'), ('146','Upstate New York'), ('147','Upstate New York'), ('148','Upstate New York'), ('149','Upstate New York'),
  -- Pittsburgh Metro: 150-168
  ('150','Pittsburgh Metro'), ('151','Pittsburgh Metro'), ('152','Pittsburgh Metro'), ('153','Pittsburgh Metro'), ('154','Pittsburgh Metro'), ('155','Pittsburgh Metro'), ('156','Pittsburgh Metro'), ('157','Pittsburgh Metro'), ('158','Pittsburgh Metro'), ('159','Pittsburgh Metro'), ('160','Pittsburgh Metro'), ('161','Pittsburgh Metro'), ('162','Pittsburgh Metro'), ('163','Pittsburgh Metro'), ('164','Pittsburgh Metro'), ('165','Pittsburgh Metro'), ('166','Pittsburgh Metro'), ('167','Pittsburgh Metro'), ('168','Pittsburgh Metro'),
  -- Philadelphia Metro: 170-196
  ('170','Philadelphia Metro'), ('171','Philadelphia Metro'), ('172','Philadelphia Metro'), ('173','Philadelphia Metro'), ('174','Philadelphia Metro'), ('175','Philadelphia Metro'), ('176','Philadelphia Metro'), ('177','Philadelphia Metro'), ('178','Philadelphia Metro'), ('179','Philadelphia Metro'), ('180','Philadelphia Metro'), ('181','Philadelphia Metro'), ('182','Philadelphia Metro'), ('183','Philadelphia Metro'), ('184','Philadelphia Metro'), ('185','Philadelphia Metro'), ('186','Philadelphia Metro'), ('187','Philadelphia Metro'), ('188','Philadelphia Metro'), ('189','Philadelphia Metro'), ('190','Philadelphia Metro'), ('191','Philadelphia Metro'), ('192','Philadelphia Metro'), ('193','Philadelphia Metro'), ('194','Philadelphia Metro'), ('195','Philadelphia Metro'), ('196','Philadelphia Metro'),
  -- Delaware: 197-199
  ('197','Delaware'), ('198','Delaware'), ('199','Delaware'),
  -- Washington DC Metro: 200-212
  ('200','Washington DC Metro'), ('201','Washington DC Metro'), ('202','Washington DC Metro'), ('203','Washington DC Metro'), ('204','Washington DC Metro'), ('205','Washington DC Metro'), ('206','Washington DC Metro'), ('207','Washington DC Metro'), ('208','Washington DC Metro'), ('209','Washington DC Metro'), ('210','Washington DC Metro'), ('211','Washington DC Metro'), ('212','Washington DC Metro'),
  -- Baltimore Metro: 213-219
  ('213','Baltimore Metro'), ('214','Baltimore Metro'), ('215','Baltimore Metro'), ('216','Baltimore Metro'), ('217','Baltimore Metro'), ('218','Baltimore Metro'), ('219','Baltimore Metro'),
  -- Virginia: 220-246
  ('220','Virginia'), ('221','Virginia'), ('222','Virginia'), ('223','Virginia'), ('224','Virginia'), ('225','Virginia'), ('226','Virginia'), ('227','Virginia'), ('228','Virginia'), ('229','Virginia'), ('230','Virginia'), ('231','Virginia'), ('232','Virginia'), ('233','Virginia'), ('234','Virginia'), ('235','Virginia'), ('236','Virginia'), ('237','Virginia'), ('238','Virginia'), ('239','Virginia'), ('240','Virginia'), ('241','Virginia'), ('242','Virginia'), ('243','Virginia'), ('244','Virginia'), ('245','Virginia'), ('246','Virginia'),
  -- West Virginia: 247-268
  ('247','West Virginia'), ('248','West Virginia'), ('249','West Virginia'), ('250','West Virginia'), ('251','West Virginia'), ('252','West Virginia'), ('253','West Virginia'), ('254','West Virginia'), ('255','West Virginia'), ('256','West Virginia'), ('257','West Virginia'), ('258','West Virginia'), ('259','West Virginia'), ('260','West Virginia'), ('261','West Virginia'), ('262','West Virginia'), ('263','West Virginia'), ('264','West Virginia'), ('265','West Virginia'), ('266','West Virginia'), ('267','West Virginia'), ('268','West Virginia'),
  -- North Carolina: 270-289
  ('270','North Carolina'), ('271','North Carolina'), ('272','North Carolina'), ('273','North Carolina'), ('274','North Carolina'), ('275','North Carolina'), ('276','North Carolina'), ('277','North Carolina'), ('278','North Carolina'), ('279','North Carolina'), ('280','North Carolina'), ('281','North Carolina'), ('282','North Carolina'), ('283','North Carolina'), ('284','North Carolina'), ('285','North Carolina'), ('286','North Carolina'), ('287','North Carolina'), ('288','North Carolina'), ('289','North Carolina'),
  -- South Carolina: 290-299
  ('290','South Carolina'), ('291','South Carolina'), ('292','South Carolina'), ('293','South Carolina'), ('294','South Carolina'), ('295','South Carolina'), ('296','South Carolina'), ('297','South Carolina'), ('298','South Carolina'), ('299','South Carolina'),
  -- Atlanta Metro: 300-319
  ('300','Atlanta Metro'), ('301','Atlanta Metro'), ('302','Atlanta Metro'), ('303','Atlanta Metro'), ('304','Atlanta Metro'), ('305','Atlanta Metro'), ('306','Atlanta Metro'), ('307','Atlanta Metro'), ('308','Atlanta Metro'), ('309','Atlanta Metro'), ('310','Atlanta Metro'), ('311','Atlanta Metro'), ('312','Atlanta Metro'), ('313','Atlanta Metro'), ('314','Atlanta Metro'), ('315','Atlanta Metro'), ('316','Atlanta Metro'), ('317','Atlanta Metro'), ('318','Atlanta Metro'), ('319','Atlanta Metro'),
  -- Florida: 320-349
  ('320','Florida'), ('321','Florida'), ('322','Florida'), ('323','Florida'), ('324','Florida'), ('325','Florida'), ('326','Florida'), ('327','Florida'), ('328','Florida'), ('329','Florida'), ('330','Florida'), ('331','Florida'), ('332','Florida'), ('333','Florida'), ('334','Florida'), ('335','Florida'), ('336','Florida'), ('337','Florida'), ('338','Florida'), ('339','Florida'), ('340','Florida'), ('341','Florida'), ('342','Florida'), ('343','Florida'), ('344','Florida'), ('345','Florida'), ('346','Florida'), ('347','Florida'), ('348','Florida'), ('349','Florida'),
  -- Alabama: 350-369
  ('350','Alabama'), ('351','Alabama'), ('352','Alabama'), ('353','Alabama'), ('354','Alabama'), ('355','Alabama'), ('356','Alabama'), ('357','Alabama'), ('358','Alabama'), ('359','Alabama'), ('360','Alabama'), ('361','Alabama'), ('362','Alabama'), ('363','Alabama'), ('364','Alabama'), ('365','Alabama'), ('366','Alabama'), ('367','Alabama'), ('368','Alabama'), ('369','Alabama'),
  -- Tennessee: 370-385
  ('370','Tennessee'), ('371','Tennessee'), ('372','Tennessee'), ('373','Tennessee'), ('374','Tennessee'), ('375','Tennessee'), ('376','Tennessee'), ('377','Tennessee'), ('378','Tennessee'), ('379','Tennessee'), ('380','Tennessee'), ('381','Tennessee'), ('382','Tennessee'), ('383','Tennessee'), ('384','Tennessee'), ('385','Tennessee'),
  -- Mississippi: 386-397
  ('386','Mississippi'), ('387','Mississippi'), ('388','Mississippi'), ('389','Mississippi'), ('390','Mississippi'), ('391','Mississippi'), ('392','Mississippi'), ('393','Mississippi'), ('394','Mississippi'), ('395','Mississippi'), ('396','Mississippi'), ('397','Mississippi'),
  -- Georgia (South): 398-399
  ('398','Georgia (South)'), ('399','Georgia (South)'),
  -- Kentucky: 400-427
  ('400','Kentucky'), ('401','Kentucky'), ('402','Kentucky'), ('403','Kentucky'), ('404','Kentucky'), ('405','Kentucky'), ('406','Kentucky'), ('407','Kentucky'), ('408','Kentucky'), ('409','Kentucky'), ('410','Kentucky'), ('411','Kentucky'), ('412','Kentucky'), ('413','Kentucky'), ('414','Kentucky'), ('415','Kentucky'), ('416','Kentucky'), ('417','Kentucky'), ('418','Kentucky'), ('419','Kentucky'), ('420','Kentucky'), ('421','Kentucky'), ('422','Kentucky'), ('423','Kentucky'), ('424','Kentucky'), ('425','Kentucky'), ('426','Kentucky'), ('427','Kentucky'),
  -- Ohio: 430-469
  ('430','Ohio'), ('431','Ohio'), ('432','Ohio'), ('433','Ohio'), ('434','Ohio'), ('435','Ohio'), ('436','Ohio'), ('437','Ohio'), ('438','Ohio'), ('439','Ohio'), ('440','Ohio'), ('441','Ohio'), ('442','Ohio'), ('443','Ohio'), ('444','Ohio'), ('445','Ohio'), ('446','Ohio'), ('447','Ohio'), ('448','Ohio'), ('449','Ohio'), ('450','Ohio'), ('451','Ohio'), ('452','Ohio'), ('453','Ohio'), ('454','Ohio'), ('455','Ohio'), ('456','Ohio'), ('457','Ohio'), ('458','Ohio'), ('459','Ohio'), ('460','Ohio'), ('461','Ohio'), ('462','Ohio'), ('463','Ohio'), ('464','Ohio'), ('465','Ohio'), ('466','Ohio'), ('467','Ohio'), ('468','Ohio'), ('469','Ohio'),
  -- Detroit Metro: 470-499
  ('470','Detroit Metro'), ('471','Detroit Metro'), ('472','Detroit Metro'), ('473','Detroit Metro'), ('474','Detroit Metro'), ('475','Detroit Metro'), ('476','Detroit Metro'), ('477','Detroit Metro'), ('478','Detroit Metro'), ('479','Detroit Metro'), ('480','Detroit Metro'), ('481','Detroit Metro'), ('482','Detroit Metro'), ('483','Detroit Metro'), ('484','Detroit Metro'), ('485','Detroit Metro'), ('486','Detroit Metro'), ('487','Detroit Metro'), ('488','Detroit Metro'), ('489','Detroit Metro'), ('490','Detroit Metro'), ('491','Detroit Metro'), ('492','Detroit Metro'), ('493','Detroit Metro'), ('494','Detroit Metro'), ('495','Detroit Metro'), ('496','Detroit Metro'), ('497','Detroit Metro'), ('498','Detroit Metro'), ('499','Detroit Metro'),
  -- Iowa: 500-528
  ('500','Iowa'), ('501','Iowa'), ('502','Iowa'), ('503','Iowa'), ('504','Iowa'), ('505','Iowa'), ('506','Iowa'), ('507','Iowa'), ('508','Iowa'), ('509','Iowa'), ('510','Iowa'), ('511','Iowa'), ('512','Iowa'), ('513','Iowa'), ('514','Iowa'), ('515','Iowa'), ('516','Iowa'), ('517','Iowa'), ('518','Iowa'), ('519','Iowa'), ('520','Iowa'), ('521','Iowa'), ('522','Iowa'), ('523','Iowa'), ('524','Iowa'), ('525','Iowa'), ('526','Iowa'), ('527','Iowa'), ('528','Iowa'),
  -- Wisconsin: 530-549
  ('530','Wisconsin'), ('531','Wisconsin'), ('532','Wisconsin'), ('533','Wisconsin'), ('534','Wisconsin'), ('535','Wisconsin'), ('536','Wisconsin'), ('537','Wisconsin'), ('538','Wisconsin'), ('539','Wisconsin'), ('540','Wisconsin'), ('541','Wisconsin'), ('542','Wisconsin'), ('543','Wisconsin'), ('544','Wisconsin'), ('545','Wisconsin'), ('546','Wisconsin'), ('547','Wisconsin'), ('548','Wisconsin'), ('549','Wisconsin'),
  -- Minneapolis Metro: 550-567
  ('550','Minneapolis Metro'), ('551','Minneapolis Metro'), ('552','Minneapolis Metro'), ('553','Minneapolis Metro'), ('554','Minneapolis Metro'), ('555','Minneapolis Metro'), ('556','Minneapolis Metro'), ('557','Minneapolis Metro'), ('558','Minneapolis Metro'), ('559','Minneapolis Metro'), ('560','Minneapolis Metro'), ('561','Minneapolis Metro'), ('562','Minneapolis Metro'), ('563','Minneapolis Metro'), ('564','Minneapolis Metro'), ('565','Minneapolis Metro'), ('566','Minneapolis Metro'), ('567','Minneapolis Metro'),
  -- North / South Dakota: 570-588
  ('570','North / South Dakota'), ('571','North / South Dakota'), ('572','North / South Dakota'), ('573','North / South Dakota'), ('574','North / South Dakota'), ('575','North / South Dakota'), ('576','North / South Dakota'), ('577','North / South Dakota'), ('578','North / South Dakota'), ('579','North / South Dakota'), ('580','North / South Dakota'), ('581','North / South Dakota'), ('582','North / South Dakota'), ('583','North / South Dakota'), ('584','North / South Dakota'), ('585','North / South Dakota'), ('586','North / South Dakota'), ('587','North / South Dakota'), ('588','North / South Dakota'),
  -- Montana: 590-599
  ('590','Montana'), ('591','Montana'), ('592','Montana'), ('593','Montana'), ('594','Montana'), ('595','Montana'), ('596','Montana'), ('597','Montana'), ('598','Montana'), ('599','Montana'),
  -- Chicago Metro: 600-629
  ('600','Chicago Metro'), ('601','Chicago Metro'), ('602','Chicago Metro'), ('603','Chicago Metro'), ('604','Chicago Metro'), ('605','Chicago Metro'), ('606','Chicago Metro'), ('607','Chicago Metro'), ('608','Chicago Metro'), ('609','Chicago Metro'), ('610','Chicago Metro'), ('611','Chicago Metro'), ('612','Chicago Metro'), ('613','Chicago Metro'), ('614','Chicago Metro'), ('615','Chicago Metro'), ('616','Chicago Metro'), ('617','Chicago Metro'), ('618','Chicago Metro'), ('619','Chicago Metro'), ('620','Chicago Metro'), ('621','Chicago Metro'), ('622','Chicago Metro'), ('623','Chicago Metro'), ('624','Chicago Metro'), ('625','Chicago Metro'), ('626','Chicago Metro'), ('627','Chicago Metro'), ('628','Chicago Metro'), ('629','Chicago Metro'),
  -- St. Louis Metro: 630-658
  ('630','St. Louis Metro'), ('631','St. Louis Metro'), ('632','St. Louis Metro'), ('633','St. Louis Metro'), ('634','St. Louis Metro'), ('635','St. Louis Metro'), ('636','St. Louis Metro'), ('637','St. Louis Metro'), ('638','St. Louis Metro'), ('639','St. Louis Metro'), ('640','St. Louis Metro'), ('641','St. Louis Metro'), ('642','St. Louis Metro'), ('643','St. Louis Metro'), ('644','St. Louis Metro'), ('645','St. Louis Metro'), ('646','St. Louis Metro'), ('647','St. Louis Metro'), ('648','St. Louis Metro'), ('649','St. Louis Metro'), ('650','St. Louis Metro'), ('651','St. Louis Metro'), ('652','St. Louis Metro'), ('653','St. Louis Metro'), ('654','St. Louis Metro'), ('655','St. Louis Metro'), ('656','St. Louis Metro'), ('657','St. Louis Metro'), ('658','St. Louis Metro'),
  -- Kansas: 660-679
  ('660','Kansas'), ('661','Kansas'), ('662','Kansas'), ('663','Kansas'), ('664','Kansas'), ('665','Kansas'), ('666','Kansas'), ('667','Kansas'), ('668','Kansas'), ('669','Kansas'), ('670','Kansas'), ('671','Kansas'), ('672','Kansas'), ('673','Kansas'), ('674','Kansas'), ('675','Kansas'), ('676','Kansas'), ('677','Kansas'), ('678','Kansas'), ('679','Kansas'),
  -- Omaha Metro: 680-693
  ('680','Omaha Metro'), ('681','Omaha Metro'), ('682','Omaha Metro'), ('683','Omaha Metro'), ('684','Omaha Metro'), ('685','Omaha Metro'), ('686','Omaha Metro'), ('687','Omaha Metro'), ('688','Omaha Metro'), ('689','Omaha Metro'), ('690','Omaha Metro'), ('691','Omaha Metro'), ('692','Omaha Metro'), ('693','Omaha Metro'),
  -- New Orleans Metro: 700-714
  ('700','New Orleans Metro'), ('701','New Orleans Metro'), ('702','New Orleans Metro'), ('703','New Orleans Metro'), ('704','New Orleans Metro'), ('705','New Orleans Metro'), ('706','New Orleans Metro'), ('707','New Orleans Metro'), ('708','New Orleans Metro'), ('709','New Orleans Metro'), ('710','New Orleans Metro'), ('711','New Orleans Metro'), ('712','New Orleans Metro'), ('713','New Orleans Metro'), ('714','New Orleans Metro'),
  -- Arkansas: 716-729
  ('716','Arkansas'), ('717','Arkansas'), ('718','Arkansas'), ('719','Arkansas'), ('720','Arkansas'), ('721','Arkansas'), ('722','Arkansas'), ('723','Arkansas'), ('724','Arkansas'), ('725','Arkansas'), ('726','Arkansas'), ('727','Arkansas'), ('728','Arkansas'), ('729','Arkansas'),
  -- Oklahoma: 730-749
  ('730','Oklahoma'), ('731','Oklahoma'), ('732','Oklahoma'), ('733','Oklahoma'), ('734','Oklahoma'), ('735','Oklahoma'), ('736','Oklahoma'), ('737','Oklahoma'), ('738','Oklahoma'), ('739','Oklahoma'), ('740','Oklahoma'), ('741','Oklahoma'), ('742','Oklahoma'), ('743','Oklahoma'), ('744','Oklahoma'), ('745','Oklahoma'), ('746','Oklahoma'), ('747','Oklahoma'), ('748','Oklahoma'), ('749','Oklahoma'),
  -- Dallas / Houston Metro: 750-799
  ('750','Dallas / Houston Metro'), ('751','Dallas / Houston Metro'), ('752','Dallas / Houston Metro'), ('753','Dallas / Houston Metro'), ('754','Dallas / Houston Metro'), ('755','Dallas / Houston Metro'), ('756','Dallas / Houston Metro'), ('757','Dallas / Houston Metro'), ('758','Dallas / Houston Metro'), ('759','Dallas / Houston Metro'), ('760','Dallas / Houston Metro'), ('761','Dallas / Houston Metro'), ('762','Dallas / Houston Metro'), ('763','Dallas / Houston Metro'), ('764','Dallas / Houston Metro'), ('765','Dallas / Houston Metro'), ('766','Dallas / Houston Metro'), ('767','Dallas / Houston Metro'), ('768','Dallas / Houston Metro'), ('769','Dallas / Houston Metro'), ('770','Dallas / Houston Metro'), ('771','Dallas / Houston Metro'), ('772','Dallas / Houston Metro'), ('773','Dallas / Houston Metro'), ('774','Dallas / Houston Metro'), ('775','Dallas / Houston Metro'), ('776','Dallas / Houston Metro'), ('777','Dallas / Houston Metro'), ('778','Dallas / Houston Metro'), ('779','Dallas / Houston Metro'), ('780','Dallas / Houston Metro'), ('781','Dallas / Houston Metro'), ('782','Dallas / Houston Metro'), ('783','Dallas / Houston Metro'), ('784','Dallas / Houston Metro'), ('785','Dallas / Houston Metro'), ('786','Dallas / Houston Metro'), ('787','Dallas / Houston Metro'), ('788','Dallas / Houston Metro'), ('789','Dallas / Houston Metro'), ('790','Dallas / Houston Metro'), ('791','Dallas / Houston Metro'), ('792','Dallas / Houston Metro'), ('793','Dallas / Houston Metro'), ('794','Dallas / Houston Metro'), ('795','Dallas / Houston Metro'), ('796','Dallas / Houston Metro'), ('797','Dallas / Houston Metro'), ('798','Dallas / Houston Metro'), ('799','Dallas / Houston Metro'),
  -- Denver Metro: 800-816
  ('800','Denver Metro'), ('801','Denver Metro'), ('802','Denver Metro'), ('803','Denver Metro'), ('804','Denver Metro'), ('805','Denver Metro'), ('806','Denver Metro'), ('807','Denver Metro'), ('808','Denver Metro'), ('809','Denver Metro'), ('810','Denver Metro'), ('811','Denver Metro'), ('812','Denver Metro'), ('813','Denver Metro'), ('814','Denver Metro'), ('815','Denver Metro'), ('816','Denver Metro'),
  -- Wyoming / Idaho: 820-838
  ('820','Wyoming / Idaho'), ('821','Wyoming / Idaho'), ('822','Wyoming / Idaho'), ('823','Wyoming / Idaho'), ('824','Wyoming / Idaho'), ('825','Wyoming / Idaho'), ('826','Wyoming / Idaho'), ('827','Wyoming / Idaho'), ('828','Wyoming / Idaho'), ('829','Wyoming / Idaho'), ('830','Wyoming / Idaho'), ('831','Wyoming / Idaho'), ('832','Wyoming / Idaho'), ('833','Wyoming / Idaho'), ('834','Wyoming / Idaho'), ('835','Wyoming / Idaho'), ('836','Wyoming / Idaho'), ('837','Wyoming / Idaho'), ('838','Wyoming / Idaho'),
  -- Salt Lake City Metro: 840-847
  ('840','Salt Lake City Metro'), ('841','Salt Lake City Metro'), ('842','Salt Lake City Metro'), ('843','Salt Lake City Metro'), ('844','Salt Lake City Metro'), ('845','Salt Lake City Metro'), ('846','Salt Lake City Metro'), ('847','Salt Lake City Metro'),
  -- Phoenix Metro: 850-865
  ('850','Phoenix Metro'), ('851','Phoenix Metro'), ('852','Phoenix Metro'), ('853','Phoenix Metro'), ('854','Phoenix Metro'), ('855','Phoenix Metro'), ('856','Phoenix Metro'), ('857','Phoenix Metro'), ('858','Phoenix Metro'), ('859','Phoenix Metro'), ('860','Phoenix Metro'), ('861','Phoenix Metro'), ('862','Phoenix Metro'), ('863','Phoenix Metro'), ('864','Phoenix Metro'), ('865','Phoenix Metro'),
  -- New Mexico: 870-884
  ('870','New Mexico'), ('871','New Mexico'), ('872','New Mexico'), ('873','New Mexico'), ('874','New Mexico'), ('875','New Mexico'), ('876','New Mexico'), ('877','New Mexico'), ('878','New Mexico'), ('879','New Mexico'), ('880','New Mexico'), ('881','New Mexico'), ('882','New Mexico'), ('883','New Mexico'), ('884','New Mexico'),
  -- Las Vegas Metro: 885-893
  ('885','Las Vegas Metro'), ('886','Las Vegas Metro'), ('887','Las Vegas Metro'), ('888','Las Vegas Metro'), ('889','Las Vegas Metro'), ('890','Las Vegas Metro'), ('891','Las Vegas Metro'), ('892','Las Vegas Metro'), ('893','Las Vegas Metro'),
  -- Los Angeles Metro: 900-928
  ('900','Los Angeles Metro'), ('901','Los Angeles Metro'), ('902','Los Angeles Metro'), ('903','Los Angeles Metro'), ('904','Los Angeles Metro'), ('905','Los Angeles Metro'), ('906','Los Angeles Metro'), ('907','Los Angeles Metro'), ('908','Los Angeles Metro'), ('909','Los Angeles Metro'), ('910','Los Angeles Metro'), ('911','Los Angeles Metro'), ('912','Los Angeles Metro'), ('913','Los Angeles Metro'), ('914','Los Angeles Metro'), ('915','Los Angeles Metro'), ('916','Los Angeles Metro'), ('917','Los Angeles Metro'), ('918','Los Angeles Metro'), ('919','Los Angeles Metro'), ('920','Los Angeles Metro'), ('921','Los Angeles Metro'), ('922','Los Angeles Metro'), ('923','Los Angeles Metro'), ('924','Los Angeles Metro'), ('925','Los Angeles Metro'), ('926','Los Angeles Metro'), ('927','Los Angeles Metro'), ('928','Los Angeles Metro'),
  -- Central California: 930-939
  ('930','Central California'), ('931','Central California'), ('932','Central California'), ('933','Central California'), ('934','Central California'), ('935','Central California'), ('936','Central California'), ('937','Central California'), ('938','Central California'), ('939','Central California'),
  -- San Francisco / Bay Area: 940-969
  ('940','San Francisco / Bay Area'), ('941','San Francisco / Bay Area'), ('942','San Francisco / Bay Area'), ('943','San Francisco / Bay Area'), ('944','San Francisco / Bay Area'), ('945','San Francisco / Bay Area'), ('946','San Francisco / Bay Area'), ('947','San Francisco / Bay Area'), ('948','San Francisco / Bay Area'), ('949','San Francisco / Bay Area'), ('950','San Francisco / Bay Area'), ('951','San Francisco / Bay Area'), ('952','San Francisco / Bay Area'), ('953','San Francisco / Bay Area'), ('954','San Francisco / Bay Area'), ('955','San Francisco / Bay Area'), ('956','San Francisco / Bay Area'), ('957','San Francisco / Bay Area'), ('958','San Francisco / Bay Area'), ('959','San Francisco / Bay Area'), ('960','San Francisco / Bay Area'), ('961','San Francisco / Bay Area'), ('962','San Francisco / Bay Area'), ('963','San Francisco / Bay Area'), ('964','San Francisco / Bay Area'), ('965','San Francisco / Bay Area'), ('966','San Francisco / Bay Area'), ('967','San Francisco / Bay Area'), ('968','San Francisco / Bay Area'), ('969','San Francisco / Bay Area'),
  -- Portland Metro: 970-979
  ('970','Portland Metro'), ('971','Portland Metro'), ('972','Portland Metro'), ('973','Portland Metro'), ('974','Portland Metro'), ('975','Portland Metro'), ('976','Portland Metro'), ('977','Portland Metro'), ('978','Portland Metro'), ('979','Portland Metro'),
  -- Seattle Metro: 980-994
  ('980','Seattle Metro'), ('981','Seattle Metro'), ('982','Seattle Metro'), ('983','Seattle Metro'), ('984','Seattle Metro'), ('985','Seattle Metro'), ('986','Seattle Metro'), ('987','Seattle Metro'), ('988','Seattle Metro'), ('989','Seattle Metro'), ('990','Seattle Metro'), ('991','Seattle Metro'), ('992','Seattle Metro'), ('993','Seattle Metro'), ('994','Seattle Metro'),
  -- Alaska: 995-999
  ('995','Alaska'), ('996','Alaska'), ('997','Alaska'), ('998','Alaska'), ('999','Alaska');

-- ── Validation ────────────────────────────────────────────────────────────────
-- SELECT COUNT(*) FROM media_advertising.gold.zip3_marketing_region;  -- → 961
-- SELECT * FROM media_advertising.gold.zip3_marketing_region WHERE zip3 = '902';  -- → 'Los Angeles Metro'
-- SELECT * FROM media_advertising.gold.zip3_marketing_region WHERE zip3 = '100';  -- → 'New York City Metro'
-- SELECT * FROM media_advertising.gold.zip3_marketing_region WHERE zip3 = '606';  -- → 'Chicago Metro'
