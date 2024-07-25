--requete1
WITH EmployeePerformance AS (
    SELECT e.EmployeeId,e.Employee_Name,d.DepartmentName,w.LocationName,e.Salary AS CurrentSalary,s.Salary AS HistoricalSalary,
        CASE 
            WHEN e.Salary > s.Salary THEN 'augmenter'
            WHEN e.Salary < s.Salary THEN 'diminuer'
            ELSE 'inchanger'
        END AS SalaryTrend
    FROM employee e JOIN department d ON e.DepartmentId = d.DepartmentId
    JOIN employeeworklocation ew ON e.EmployeeId = ew.WorkEmployeeId
    JOIN worklocation w ON ew.LocationId = w.LocationId
    LEFT JOIN salary s ON e.EmployeeId = s.EmployeeId
),
DepartmentStats AS (
    SELECT DepartmentName,AVG(CurrentSalary) AS AvgDepartmentSalary,COUNT(*) AS EmployeeCount
    FROM EmployeePerformance GROUP BY DepartmentName
),
LocationStats AS (
    SELECT LocationName,AVG(CurrentSalary) AS AvgLocationSalary, COUNT(*) AS EmployeeCount
    FROM EmployeePerformance GROUP BY LocationName
)
SELECT ep.EmployeeId,ep.Employee_Name,ep.DepartmentName,ep.LocationName,ep.CurrentSalary,ep.SalaryTrend,
    ds.AvgDepartmentSalary,ls.AvgLocationSalary,
    CASE 
        WHEN ep.CurrentSalary > ds.AvgDepartmentSalary THEN 'plus'
        WHEN ep.CurrentSalary < ds.AvgDepartmentSalary THEN 'moins'
        ELSE 'egale'
    END AS DepartmentSalaryComparison,
    CASE 
        WHEN ep.CurrentSalary > ls.AvgLocationSalary THEN 'plus'
        WHEN ep.CurrentSalary < ls.AvgLocationSalary THEN 'moins'
        ELSE 'egale'
    END AS LocationSalaryComparison
FROM EmployeePerformance ep
JOIN DepartmentStats ds ON ep.DepartmentName = ds.DepartmentName
JOIN LocationStats ls ON ep.LocationName = ls.LocationName
ORDER BY ep.DepartmentName, ep.CurrentSalary DESC;
-------
--requete2(customers with high-value plans and their call durations:)
WITH HighValueCustomers AS (
    SELECT c.CustomerId, c.CustomerName, p.PlansType, p.PlanName
    FROM customer c
    JOIN simdata sd ON c.CustomerId = sd.SimCustomerId
    JOIN plans p ON sd.SimPlanNumber = p.PlansId
    JOIN planinclusions pi ON p.PlanInclusionId = pi.PlanId
    WHERE pi.Data LIKE '%GB%' AND 
          TRY_CAST(CASE 
              WHEN CHARINDEX(' ', pi.Data) > 1 
              THEN LEFT(pi.Data, CHARINDEX(' ', pi.Data) - 1) 
              ELSE pi.Data 
          END AS DECIMAL) >= 1.5
)
SELECT hvc.CustomerName, hvc.PlansType, hvc.PlanName,
       SUM(DATEDIFF(SECOND, cr.CallStartTime, cr.CallEndTime)) AS TotalCallDurationSeconds
FROM HighValueCustomers hvc
JOIN simdata sd ON hvc.CustomerId = sd.SimCustomerId
JOIN phonenumber pn ON sd.SimAccountNumber = pn.AccountNumber
JOIN callrecords cr ON pn.AccountNumber = cr.CallAccountNumber
GROUP BY hvc.CustomerName, hvc.PlansType, hvc.PlanName
ORDER BY TotalCallDurationSeconds DESC;
--requete3(top-performing salespeople)
SELECT 
	sp.SalesPersonId,e.Employee_Name AS SalespersonName,COUNT(DISTINCT c.CustomerId) AS TotalCustomers,
    AVG(e.Salary) AS AverageSalary,
    (SELECT COUNT(DISTINCT o.OrderId)
     FROM orders o
     WHERE o.OrderCustomerId IN (SELECT CustomerId FROM customer WHERE CustomerSalesPersonId = sp.SalesPersonId)
    ) AS TotalOrders,
    (SELECT TOP 1 w.LocationName
     FROM employeeworklocation ew
     JOIN worklocation w ON ew.LocationId = w.LocationId
     WHERE ew.WorkEmployeeId = sp.IdEmployeeSalesPerson
    ) AS PrimaryWorkLocation
FROM salesperson sp
JOIN employee e ON sp.IdEmployeeSalesPerson = e.EmployeeId
JOIN customer c ON sp.SalesPersonId = c.CustomerSalesPersonId
GROUP BY sp.SalesPersonId, sp.IdEmployeeSalesPerson, e.Employee_Name, e.Salary
HAVING COUNT(DISTINCT c.CustomerId) > 3 ORDER BY TotalCustomers DESC, AverageSalary DESC;

--requete4
WITH CustomerCallStats AS (
    SELECT c.CustomerId,c.CustomerName,sd.SimNumber,p.PlanName,
        pi.Data AS PlanData,pi.Talktime AS PlanTalktime, COUNT(cr.CallId) AS TotalCalls,
        SUM(DATEDIFF(SECOND, cr.CallStartTime, cr.CallEndTime)) AS TotalCallDurationSeconds,
        AVG(DATEDIFF(SECOND, cr.CallStartTime, cr.CallEndTime)) AS AvgCallDurationSeconds,
        ROW_NUMBER() OVER (PARTITION BY c.CustomerId ORDER BY COUNT(cr.CallId) DESC) AS PlanRank
    FROM customer c
    JOIN simdata sd ON c.CustomerId = sd.SimCustomerId
    JOIN plans p ON sd.SimPlanNumber = p.PlansId
    JOIN planinclusions pi ON p.PlanInclusionId = pi.PlanId
    JOIN phonenumber pn ON sd.SimAccountNumber = pn.AccountNumber
    LEFT JOIN callrecords cr ON pn.AccountNumber = cr.CallAccountNumber
    GROUP BY c.CustomerId, c.CustomerName, sd.SimNumber, p.PlanName, pi.Data, pi.Talktime
),
CustomerBillingInfo AS (
    SELECT ccs.CustomerId,ccs.CustomerName,ccs.SimNumber,ccs.PlanName,ccs.PlanData,ccs.PlanTalktime,
        ccs.TotalCalls,ccs.TotalCallDurationSeconds,ccs.AvgCallDurationSeconds,bi.IncludedData,
        bi.DataUsed,bi.BalancedData,bi.Tax
    FROM CustomerCallStats ccs
    JOIN phonenumber pn ON ccs.SimNumber = pn.PhoneNumber
    JOIN billinginformation bi ON pn.PhoneBillNumber = bi.BillNumber
    WHERE ccs.PlanRank = 1
)
SELECT 
    cbi.*,
    CASE 
        WHEN CAST(SUBSTRING(cbi.PlanTalktime, 1, CHARINDEX(' ', cbi.PlanTalktime) - 1) AS INT) * 60 < cbi.TotalCallDurationSeconds THEN 'Exceeding'
        ELSE 'Within Limit'
    END AS TalktimeStatus,
    CASE 
        WHEN cbi.DataUsed > cbi.IncludedData THEN 'Exceeding'
        ELSE 'Within Limit'
    END AS DataUsageStatus,
    DENSE_RANK() OVER (ORDER BY cbi.TotalCalls DESC) AS CallFrequencyRank,
    DENSE_RANK() OVER (ORDER BY cbi.DataUsed DESC) AS DataUsageRank
FROM CustomerBillingInfo cbi
ORDER BY cbi.TotalCalls DESC, cbi.DataUsed DESC;

--requete5( hierarchical view of employee-manager relationships)
WITH EmployeeHierarchy AS (
    SELECT e.EmployeeId, e.Employee_Name,e.DepartmentId,d.DepartmentName,
        e.Salary,CAST(e.Employee_Name AS VARCHAR(255)) AS HierarchyPath,0 AS Level
    FROM employee e
    JOIN department d ON e.DepartmentId = d.DepartmentId
    WHERE e.EmployeeId NOT IN (SELECT DISTINCT IdEmployeeSalesPerson FROM salesperson)
    
    UNION ALL
    
    SELECT e.EmployeeId,e.Employee_Name,e.DepartmentId,d.DepartmentName,e.Salary,
        CAST(eh.HierarchyPath + ' > ' + e.Employee_Name AS VARCHAR(255)),
        eh.Level + 1
    FROM employee e
    JOIN department d ON e.DepartmentId = d.DepartmentId
    JOIN salesperson sp ON e.EmployeeId = sp.IdEmployeeSalesPerson
    JOIN EmployeeHierarchy eh ON sp.SalesPersonId = eh.EmployeeId
    WHERE e.EmployeeId <> eh.EmployeeId
)
SELECT 
    eh.*,w.LocationName,COUNT(c.CustomerId) AS ManagedCustomers,AVG(CAST(c.Age AS FLOAT)) AS AvgCustomerAge
FROM EmployeeHierarchy eh
LEFT JOIN employeeworklocation ew ON eh.EmployeeId = ew.WorkEmployeeId
LEFT JOIN worklocation w ON ew.LocationId = w.LocationId
LEFT JOIN salesperson sp ON eh.EmployeeId = sp.IdEmployeeSalesPerson
LEFT JOIN customer c ON sp.SalesPersonId = c.CustomerSalesPersonId
GROUP BY eh.EmployeeId, eh.Employee_Name, eh.DepartmentId, eh.DepartmentName, eh.Salary, eh.HierarchyPath, eh.Level, w.LocationName
ORDER BY eh.Level, eh.DepartmentId, eh.Salary DESC;
--requete6
WITH OrderTrends AS (
    SELECT 
        YEAR(c.DateOfBirth) AS BirthYear,c.Sex,o.OrderType,o.OrderStatus,
        COUNT(*) AS OrderCount,AVG(DATEDIFF(YEAR, c.DateOfBirth, GETDATE())) AS AvgCustomerAge
    FROM customer c
    JOIN orders o ON c.CustomerId = o.OrderCustomerId
    GROUP BY YEAR(c.DateOfBirth), c.Sex, o.OrderType, o.OrderStatus
),
SalespersonPerformance AS (
    SELECT 
        sp.SalesPersonId,e.Employee_Name AS SalespersonName,d.DepartmentName,
        COUNT(DISTINCT c.CustomerId) AS TotalCustomers,COUNT(DISTINCT o.OrderId) AS TotalOrders,
        SUM(CASE WHEN o.OrderStatus = 'Shipped' THEN 1 ELSE 0 END) AS ShippedOrders,
        AVG(DATEDIFF(YEAR, c.DateOfBirth, GETDATE())) AS AvgCustomerAge
    FROM salesperson sp
    JOIN employee e ON sp.IdEmployeeSalesPerson = e.EmployeeId
    JOIN department d ON e.DepartmentId = d.DepartmentId
    LEFT JOIN customer c ON sp.SalesPersonId = c.CustomerSalesPersonId
    LEFT JOIN orders o ON c.CustomerId = o.OrderCustomerId
    GROUP BY sp.SalesPersonId, e.Employee_Name, d.DepartmentName
)
SELECT ot.BirthYear,ot.Sex,ot.OrderType,ot.OrderStatus,ot.OrderCount,ot.AvgCustomerAge,sp.SalespersonName,sp.DepartmentName,sp.TotalCustomers,
    sp.TotalOrders,sp.ShippedOrders,CAST(sp.ShippedOrders AS FLOAT) / NULLIF(sp.TotalOrders, 0) AS ShippedOrderRate,
    DENSE_RANK() OVER (ORDER BY sp.TotalCustomers DESC) AS CustomerRank,
    DENSE_RANK() OVER (ORDER BY sp.TotalOrders DESC) AS OrderRank,
    DENSE_RANK() OVER (ORDER BY CAST(sp.ShippedOrders AS FLOAT) / NULLIF(sp.TotalOrders, 0) DESC) AS ShippedOrderRateRank
FROM OrderTrends ot
CROSS APPLY (
    SELECT TOP 1 *
    FROM SalespersonPerformance
    WHERE AvgCustomerAge BETWEEN ot.AvgCustomerAge - 5 AND ot.AvgCustomerAge + 5
    ORDER BY TotalOrders DESC
) sp
ORDER BY ot.BirthYear, ot.Sex, ot.OrderCount DESC;

--requete7 (pivot)
WITH PlanDetails AS (
    SELECT  p.PlansId,p.PlansType,p.PlanName,pi.Data,pi.Talktime,pi.TextMessages
    FROM plans p
    JOIN planinclusions pi ON p.PlanInclusionId = pi.PlanId
),
PivotedPlans AS (
    SELECT *
    FROM (
        SELECT 
            PlansId,PlansType,PlanName,'Data' AS InclusionType,Data AS InclusionValue
        FROM PlanDetails
        UNION ALL
        SELECT 
            PlansId,PlansType,PlanName,'Talktime' AS InclusionType,Talktime AS InclusionValue
        FROM PlanDetails
        UNION ALL
        SELECT 
            PlansId,PlansType,PlanName,'TextMessages' AS InclusionType,TextMessages AS InclusionValue
        FROM PlanDetails
    ) AS SourceTable
    PIVOT (
        MAX(InclusionValue)
        FOR InclusionType IN ([Data], [Talktime], [TextMessages])
    ) AS PivotTable
)
SELECT 
    pp.*,COUNT(DISTINCT sd.SimCustomerId) AS TotalCustomers,
    AVG(DATEDIFF(YEAR, c.DateOfBirth, GETDATE())) AS AvgCustomerAge,
    SUM(CASE WHEN o.OrderStatus = 'Shipped' THEN 1 ELSE 0 END) AS TotalShippedOrders,
    AVG(bi.DataUsed) AS AvgDataUsed,
    AVG(bi.Tax) AS AvgTax
FROM PivotedPlans pp
LEFT JOIN simdata sd ON pp.PlansId = sd.SimPlanNumber
LEFT JOIN customer c ON sd.SimCustomerId = c.CustomerId
LEFT JOIN orders o ON c.CustomerId = o.OrderCustomerId
LEFT JOIN phonenumber pn ON sd.SimAccountNumber = pn.AccountNumber
LEFT JOIN billinginformation bi ON pn.PhoneBillNumber = bi.BillNumber
GROUP BY pp.PlansId, pp.PlansType, pp.PlanName, pp.[Data], pp.Talktime, pp.TextMessages
ORDER BY TotalCustomers DESC, AvgDataUsed DESC;
--requete8
SELECT 
    c.CustomerId,c.CustomerName,sd.SimNumber,p.PlanName,bi.IncludedData,bi.DataUsed,
    (SELECT AVG(DataUsed) 
     FROM billinginformation 
     WHERE BillNumber IN (
         SELECT PhoneBillNumber 
         FROM phonenumber 
         WHERE AccountNumber IN (
             SELECT SimAccountNumber 
             FROM simdata 
             WHERE SimCustomerId = c.CustomerId
         )
     )) AS AvgDataUsed,
    (SELECT COUNT(*) 
     FROM callrecords cr
     JOIN phonenumber pn ON cr.CallAccountNumber = pn.AccountNumber
     WHERE pn.AccountNumber = sd.SimAccountNumber
     AND DATEDIFF(SECOND, cr.CallStartTime, cr.CallEndTime) > 
         (SELECT AVG(DATEDIFF(SECOND, CallStartTime, CallEndTime)) 
          FROM callrecords)
    ) AS LongCalls,
    (SELECT TOP 1 OrderStatus
     FROM orders
     WHERE OrderCustomerId = c.CustomerId
     ORDER BY OrderId DESC
    ) AS LatestOrderStatus
FROM customer c
JOIN simdata sd ON c.CustomerId = sd.SimCustomerId
JOIN plans p ON sd.SimPlanNumber = p.PlansId
JOIN phonenumber pn ON sd.SimAccountNumber = pn.AccountNumber
JOIN billinginformation bi ON pn.PhoneBillNumber = bi.BillNumber
WHERE c.CustomerId IN (
    SELECT TOP 5 SimCustomerId
    FROM simdata
    GROUP BY SimCustomerId
    ORDER BY COUNT(*) DESC
)
AND bi.DataUsed > (
    SELECT AVG(DataUsed)
    FROM billinginformation
);

