---REQUETES SQL

--requete1
SELECT c.customername, sum(cast(substring(p.talktime, 1, charindex(' ', p.talktime)) AS INT)) AS total_talktime_minutes
FROM customer c
INNER JOIN simdata s ON s.simcustomerid = c.customerid
INNER JOIN plans pl ON s.simplannumber = pl.plansid
INNER JOIN planinclusions p ON pl.planinclusionid = p.planid
GROUP BY c.customername
ORDER BY total_talktime_minutes;

--requete2
SELECT sp.salespersonid, max(c.customername) AS max_customername,
       sum(cast(substring(p.talktime, 1, charindex(' ', p.talktime)) AS INT)) AS total_talktime_minutes
FROM salesperson sp INNER JOIN customer c ON sp.salespersonid = c.customersalespersonid
INNER JOIN simdata s ON s.simcustomerid = c.customerid
LEFT JOIN plans pl ON s.simplannumber = pl.plansid
INNER JOIN planinclusions p ON pl.planinclusionid = p.planid
GROUP BY sp.salespersonid
ORDER BY sp.salespersonid;

--requete3:
SELECT sp.salespersonid,c.customername,
       sum(cast(substring(p.talktime, 1, charindex(' ', p.talktime)) AS INT)) AS total_talktime
FROM salesperson sp
INNER JOIN customer c ON sp.salespersonid = c.customersalespersonid
INNER JOIN simdata s ON s.simcustomerid = c.customerid
LEFT JOIN plans pl ON s.simplannumber = pl.plansid
INNER JOIN planinclusions p ON pl.planinclusionid = p.planid
GROUP BY sp.salespersonid, c.customername
ORDER BY sp.salespersonid;

---requete4:
SELECT sp.salespersonid,c.customername,
       sum(cast(substring(p.talktime, 1, charindex(' ', p.talktime)) AS INT)) AS total_talktime
FROM salesperson sp
INNER JOIN customer c ON sp.salespersonid = c.customersalespersonid
INNER JOIN simdata s ON s.simcustomerid = c.customerid
LEFT JOIN plans pl ON s.simplannumber = pl.plansid
INNER JOIN planinclusions p ON pl.planinclusionid = p.planid
GROUP BY sp.salespersonid, c.customername
ORDER BY sp.salespersonid;

---requete5:
SELECT w.locationname,COUNT(o.orderid) AS order_count,
      'on the way' AS tracking_status,
       SUM(e.salary) AS total_salary
FROM worklocation w 
LEFT JOIN employeeworklocation ew ON w.locationid = ew.locationid 
LEFT JOIN employee e ON e.employeeid = ew.workemployeeid 
LEFT JOIN salesperson sp ON e.employeeid = sp.idemployeesalesperson 
LEFT JOIN customer c ON sp.salespersonid = c.customersalespersonid 
LEFT JOIN orders o ON o.ordercustomerid = c.customerid 
LEFT JOIN tracking t ON o.orderid = t.trackingorderid 
WHERE t.trackingstatus = 'on the way' 
GROUP BY w.locationname ORDER BY SUM(e.salary);

---requete6:
SELECT 
    e.employee_name,
    string_agg(c.customername, ', ') AS customer_names,
    sum(datediff(second, '00:00:00', ca.callduration)) AS total_call_duration_seconds
FROM employee e LEFT JOIN salesperson sp ON sp.salespersonid = e.employeeid 
LEFT JOIN customer c ON c.customersalespersonid = sp.salespersonid 
LEFT JOIN simdata d ON c.customerid = d.simcustomerid 
LEFT JOIN phonenumber p ON d.simaccountnumber = p.accountnumber 
LEFT JOIN callrecords ca ON p.accountnumber = ca.callaccountnumber 
GROUP BY e.employee_name ORDER BY total_call_duration_seconds DESC;

--requete7:
SELECT 
    c.customername,
    c.customerid AS id 
FROM customer c 
LEFT JOIN simdata dt ON c.customerid = dt.simcustomerid 
LEFT JOIN phonenumber p ON p.accountnumber = dt.simaccountnumber 
LEFT JOIN callrecords r ON p.accountnumber = r.callaccountnumber 
WHERE datediff(second, '00:00:00', r.callduration) >= (SELECT max(datediff(second, '00:00:00', r2.callduration)) FROM callrecords r2 WHERE DATEDIFF(SECOND, '00:00:00', r2.callduration) >= 1000);

--requete8:
SELECT distinct(c.customername), c.customerid AS id 
FROM customer c 
LEFT JOIN simdata dt ON c.customerid = dt.simcustomerid 
LEFT JOIN phonenumber p ON p.accountnumber = dt.simaccountnumber 
LEFT JOIN callrecords r ON p.accountnumber = r.callaccountnumber 
WHERE datediff(second, '00:00:00', r.callduration) IN (
        SELECT datediff(second, '00:00:00', callduration) 
        FROM callrecords 
        WHERE datediff(second, '00:00:00', callduration) >= 1000);

--requete9:
SELECT 
    c.customername, 
    max(c.customerid) AS id 
FROM customer c 
LEFT JOIN simdata dt ON c.customerid = dt.simcustomerid 
LEFT JOIN phonenumber p ON p.accountnumber = dt.simaccountnumber 
LEFT JOIN callrecords r ON p.accountnumber = r.callaccountnumber 
WHERE datediff(second, '00:00:00', r.callduration) <= (
        SELECT 
            avg(datediff(second, '00:00:00', callduration))
        FROM 
            callrecords
    )
GROUP BY c.customername;

--requete10:
SELECT 
    w.locationname,count(o.orderid) AS total_orders,
    t.trackingstatus,sum(s.salary) AS total_salary
FROM worklocation w
LEFT JOIN employeeworklocation ew ON w.locationid = ew.locationid
LEFT JOIN employee e ON e.employeeid = ew.workemployeeid
LEFT JOIN salary s ON e.departmentid = s.departmentid
LEFT JOIN salesperson sp ON e.employeeid = sp.idemployeesalesperson
LEFT JOIN customer c ON sp.salespersonid = c.customersalespersonid
LEFT JOIN orders o ON o.ordercustomerid = c.customerid
LEFT JOIN tracking t ON o.orderid = t.trackingorderid
WHERE t.trackingstatus = 'on the way'
GROUP BY w.locationname, t.trackingstatus
ORDER BY sum(s.salary);

--requete11:
WITH SalespersonSales AS (
    SELECT sp.SalesPersonId, e.Employee_Name AS SalesPersonName, sum(bi.BalancedData) AS TotalSales
    FROM salesperson sp
    LEFT JOIN employee e ON sp.IdEmployeeSalesPerson = e.EmployeeId
    LEFT JOIN customer c ON sp.SalesPersonId = c.CustomerSalesPersonId
    LEFT JOIN orders o ON c.CustomerId = o.OrderCustomerId
    LEFT JOIN billinginformation bi ON o.OrderId = bi.BillNumber
    GROUP BY sp.SalesPersonId, e.Employee_Name
)
SELECT SalesPersonId,SalesPersonName,TotalSales
FROM SalespersonSales ORDER BY TotalSales DESC;

--requete12:
WITH SalespersonSales AS (
    SELECT sp.SalesPersonId, e.Employee_Name AS SalesPersonName, sum(bi.DataUsed) AS TotalSales
    FROM salesperson sp
    LEFT JOIN employee e ON sp.IdEmployeeSalesPerson = e.EmployeeId
    LEFT JOIN customer c ON sp.SalesPersonId = c.CustomerSalesPersonId
    LEFT JOIN orders o ON c.CustomerId = o.OrderCustomerId
    LEFT JOIN billinginformation bi ON o.OrderId = bi.BillNumber
    GROUP BY sp.SalesPersonId, e.Employee_Name
)
SELECT SalesPersonId,SalesPersonName,TotalSales
FROM SalespersonSales ORDER BY TotalSales DESC;

--requete13:
WITH CustomerDataUsage AS (
    SELECT c.CustomerId,c.CustomerName,SUM(bi.DataUsed) OVER (PARTITION BY c.CustomerId) AS TotalDataUsage,
        ROW_NUMBER() OVER (ORDER BY SUM(bi.DataUsed) DESC) AS Rank
    FROM customer c
    JOIN orders o ON c.CustomerId = o.OrderCustomerId
    JOIN billinginformation bi ON o.OrderId = bi.BillNumber
    GROUP BY c.CustomerId, c.CustomerName, bi.DataUsed
)
SELECT CustomerId,CustomerName,TotalDataUsage,Rank
FROM CustomerDataUsage
WHERE Rank <= 3
ORDER BY TotalDataUsage DESC;

--requete14:
WITH EmployeeDetails AS (
    SELECT e.EmployeeId,e.Employee_Name,
        e.Salary,ROW_NUMBER() OVER (ORDER BY e.EmployeeId) AS RowNum,
        LAG(e.EmployeeId) OVER (ORDER BY e.EmployeeId) AS PreviousEmployeeId,
        LEAD(e.EmployeeId) OVER (ORDER BY e.EmployeeId) AS NextEmployeeId
    FROM employee e
)
SELECT EmployeeId,Employee_Name,Salary,
    PreviousEmployeeId,NextEmployeeId,
    ABS(EmployeeId - PreviousEmployeeId) AS GapToPreviousEmployee,
    ABS(EmployeeId - NextEmployeeId) AS GapToNextEmployee
FROM EmployeeDetails ORDER BY EmployeeId;

--requete15:
WITH RankedEmployees AS (
    SELECT e.EmployeeId,e.Employee_Name,e.Salary,e.DepartmentId,
        ROW_NUMBER() OVER (PARTITION BY e.DepartmentId ORDER BY e.Salary DESC) AS Rank
    FROM employee e
)
SELECT DepartmentId,EmployeeId,Employee_Name,Salary,rank
FROM RankedEmployees
WHERE Rank <= 5
ORDER BY DepartmentId, Rank;

--requete16:
SELECT EmployeeId,Employee_Name,Salary,DepartmentId,
    DENSE_RANK() OVER (PARTITION BY DepartmentId ORDER BY Salary DESC) AS SalaryRankInDepartment,
    ROW_NUMBER() OVER (PARTITION BY DepartmentId ORDER BY Salary DESC) AS SalaryRowInDepartment,
    NTILE(4) OVER (PARTITION BY DepartmentId ORDER BY Salary DESC) AS SalaryQuartileInDepartment,
    Salary - AVG(Salary) OVER (PARTITION BY DepartmentId) AS SalaryDifferenceFromAvg,
    FIRST_VALUE(EmployeeId) OVER (PARTITION BY DepartmentId ORDER BY Salary DESC) AS HighestPaidEmployeeIdInDepartment,
    LAST_VALUE(EmployeeId) OVER (PARTITION BY DepartmentId ORDER BY Salary DESC) AS LowestPaidEmployeeIdInDepartment
FROM employee;

--requete17:
SELECT CustomerId,CustomerName, TotalOrderCost,
    RANK() OVER (ORDER BY TotalOrderCost DESC) AS CustomerRank,
    TotalOrderCost / SUM(TotalOrderCost) OVER () * 100 AS OrderCostPercentage
FROM
    (SELECT c.CustomerId,c.CustomerName,
            SUM(bi.BalancedData) AS TotalOrderCost,
            DENSE_RANK() OVER (PARTITION BY c.CustomerId ORDER BY SUM(bi.BalancedData) DESC) AS CustomerOrderRank
        FROM customer c
        LEFT JOIN orders o ON c.CustomerId = o.OrderCustomerId
        LEFT JOIN billinginformation bi ON o.OrderId = bi.BillNumber
        GROUP BY c.CustomerId, c.CustomerName
    ) AS CustomerOrderStats WHERE CustomerOrderRank = 1;

--requete18:
SELECT e.EmployeeId,e.Employee_Name,e.DepartmentId,e.Salary,e.Age,
    e.SSN,ROW_NUMBER() OVER (ORDER BY e.Salary DESC) AS RowNumber
FROM employee e JOIN department d ON e.DepartmentId = d.DepartmentId
WHERE e.Employee_Name LIKE '[A-M]%' ORDER BY e.Age DESC
OFFSET 10 ROWS FETCH NEXT 5 ROWS ONLY;

--requete19:
SELECT COALESCE(Employee_Name, 'inconnu') AS EmployeeName,
    DepartmentId,FORMAT(Salary, 'C', 'en-US') AS FormattedSalary,
    CONCAT('Department_', DepartmentId) AS DepartmentCode,
    DATEADD(MONTH, 3, GETDATE()) AS HiredDatePlus3Months
FROM employee;

--requete20:
WITH OrderTrends AS (
    SELECT 
        YEAR(c.DateOfBirth) AS BirthYear,
        c.Sex,
        o.OrderType,
        o.OrderStatus,
        COUNT(*) AS OrderCount,
        AVG(DATEDIFF(YEAR, c.DateOfBirth, GETDATE())) AS AvgCustomerAge
    FROM customer c
    JOIN orders o ON c.CustomerId = o.OrderCustomerId
    GROUP BY YEAR(c.DateOfBirth), c.Sex, o.OrderType, o.OrderStatus
),
SalespersonPerformance AS (
    SELECT 
        sp.SalesPersonId,
        e.Employee_Name AS SalespersonName,
        d.DepartmentName,
        COUNT(DISTINCT c.CustomerId) AS TotalCustomers,
        COUNT(DISTINCT o.OrderId) AS TotalOrders,
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
    sp.TotalOrders,sp.ShippedOrders,
    CAST(sp.ShippedOrders AS FLOAT) / NULLIF(sp.TotalOrders, 0) AS ShippedOrderRate,
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

--requete21:
WITH OrderTrends AS (
    SELECT 
        YEAR(c.DateOfBirth) AS BirthYear,
        c.Sex,
        o.OrderType,
        o.OrderStatus,
        COUNT(*) AS OrderCount,
        AVG(DATEDIFF(YEAR, c.DateOfBirth, GETDATE())) AS AvgCustomerAge
    FROM customer c
    JOIN orders o ON c.CustomerId = o.OrderCustomerId
    GROUP BY YEAR(c.DateOfBirth), c.Sex, o.OrderType, o.OrderStatus
),
SalespersonPerformance AS (
    SELECT 
        sp.SalesPersonId,
        e.Employee_Name AS SalespersonName,
        d.DepartmentName,
        COUNT(DISTINCT c.CustomerId) AS TotalCustomers,
        COUNT(DISTINCT o.OrderId) AS TotalOrders,
        SUM(CASE WHEN o.OrderStatus = 'Shipped' THEN 1 ELSE 0 END) AS ShippedOrders,
        AVG(DATEDIFF(YEAR, c.DateOfBirth, GETDATE())) AS AvgCustomerAge
    FROM salesperson sp
    JOIN employee e ON sp.IdEmployeeSalesPerson = e.EmployeeId
    JOIN department d ON e.DepartmentId = d.DepartmentId
    LEFT JOIN customer c ON sp.SalesPersonId = c.CustomerSalesPersonId
    LEFT JOIN orders o ON c.CustomerId = o.OrderCustomerId
    GROUP BY sp.SalesPersonId, e.Employee_Name, d.DepartmentName
)
SELECT ot.BirthYear,ot.Sex,ot.OrderType,ot.OrderStatus,ot.OrderCount,ot.AvgCustomerAge,
    sp.SalespersonName,sp.DepartmentName,sp.TotalCustomers,sp.TotalOrders,sp.ShippedOrders,
    CAST(sp.ShippedOrders AS FLOAT) / NULLIF(sp.TotalOrders, 0) AS ShippedOrderRate,
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

--requete22:
SELECT c.CustomerId,c.CustomerName,o.OrderId,o.OrderType,o.OrderStatus,bi.TotalCost
FROM customer c
JOIN orders o ON c.CustomerId = o.OrderCustomerId
JOIN (SELECT OrderCustomerId, SUM(IncludedData + DataUsed + BalancedData) AS TotalCost
     FROM orders o
     JOIN billinginformation bi ON o.OrderId = bi.BillNumber
     GROUP BY OrderCustomerId) AS bi ON c.CustomerId = bi.OrderCustomerId
WHERE bi.TotalCost > (SELECT AVG(TotalCost) 
FROM (SELECT SUM(IncludedData + DataUsed + BalancedData) AS TotalCost FROM billinginformation GROUP BY BillNumber) AS avgCost)
ORDER BY bi.TotalCost DESC;

