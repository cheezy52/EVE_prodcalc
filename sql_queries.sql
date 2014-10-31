#Match item name to item ID
SELECT "typeID", "typeName" 
FROM "invTypes" 
WHERE "typeName" = 'Atron'

#Find materials to build a given item ID
#activityID = 1 for manufacturing
SELECT iam."materialTypeID", iam."quantity", it."typeName"
FROM "industryActivityProducts" iap
JOIN "industryActivityMaterials" iam
ON iap."typeID" = iam."typeID"
AND iam."activityID" = 1
JOIN "invTypes" it
ON iam."materialTypeID" = it."typeID"
WHERE "productTypeID" = 608

#Find materials to build a given item by name (using subquery)
SELECT iam."materialTypeID", iam."quantity", it."typeName"
FROM "industryActivityProducts" iap
JOIN "industryActivityMaterials" iam
ON iap."typeID" = iam."typeID"
AND iam."activityID" = 1
JOIN "invTypes" it
ON iam."materialTypeID" = it."typeID"
WHERE "productTypeID" = (
SELECT "typeID"
FROM "invTypes"
WHERE "typeName" = 'Atron')

#Find manufacturing duration for a given item ID
SELECT "time"
FROM "industryActivity" ia
JOIN "industryActivityProducts" iap
ON ia."typeID" = iap."typeID"
WHERE iap."productTypeID" = 608
AND ia."activityID" = 1

#Find manufacturing duration for a given item name
SELECT "time", "typeName"
FROM "industryActivity" ia
JOIN "industryActivityProducts" iap
ON ia."typeID" = iap."typeID"
JOIN "invTypes" it
ON iap."productTypeID" = it."typeID"
WHERE it."typeName" = 'Atron'
AND ia."activityID" = 1

#Find blueprint typeID for an output item typeID
SELECT "typeID"
FROM "industryActivityProducts"
WHERE "productTypeID" = 608

#...or name
SELECT iap."typeID"
FROM "industryActivityProducts" iap
JOIN "invTypes" it
ON it."typeID" = iap."productTypeID"
WHERE it."typeName" = 'Atron'