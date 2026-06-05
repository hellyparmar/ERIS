/**
 * Enterprise Retail Intelligence System v3.0
 * CUSTOMER DATA - Mock Customer Database
 */

// Helper function to generate random date within range
const randomDate = (start, end) => {
    return new Date(start.getTime() + Math.random() * (end.getTime() - start.getTime()));
};

// Indian names for realistic data
const firstNames = [
    'Rajesh', 'Priya', 'Amit', 'Sneha', 'Vikram', 'Anjali', 'Arjun', 'Kavya',
    'Rahul', 'Divya', 'Karan', 'Pooja', 'Rohan', 'Neha', 'Sanjay', 'Ritu',
    'Aditya', 'Meera', 'Varun', 'Ishita', 'Nikhil', 'Shreya', 'Manish', 'Ananya',
    'Suresh', 'Deepika', 'Akash', 'Simran', 'Vishal', 'Tanvi', 'Gaurav', 'Nisha',
    'Harsh', 'Aarti', 'Mohit', 'Swati', 'Abhishek', 'Riya', 'Siddharth', 'Megha'
];

const lastNames = [
    'Sharma', 'Patel', 'Kumar', 'Singh', 'Gupta', 'Reddy', 'Iyer', 'Joshi',
    'Mehta', 'Nair', 'Rao', 'Verma', 'Agarwal', 'Desai', 'Kulkarni', 'Pandey',
    'Malhotra', 'Chopra', 'Bose', 'Menon', 'Sinha', 'Kapoor', 'Bansal', 'Shah'
];

const cities = [
    'Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 'Kolkata',
    'Pune', 'Ahmedabad', 'Jaipur', 'Surat', 'Lucknow', 'Kanpur',
    'Nagpur', 'Indore', 'Thane', 'Bhopal', 'Visakhapatnam', 'Vadodara'
];

const categories = [
    'Electronics', 'Fashion', 'Home & Kitchen', 'Books', 'Sports',
    'Beauty & Personal Care', 'Groceries', 'Toys', 'Automotive'
];

const genders = ['Male', 'Female', 'Other'];

// Generate mock customers
const generateCustomers = (count = 120) => {
    const customers = [];
    const today = new Date();
    const twoYearsAgo = new Date(today.getFullYear() - 2, today.getMonth(), today.getDate());

    for (let i = 0; i < count; i++) {
        const firstName = firstNames[Math.floor(Math.random() * firstNames.length)];
        const lastName = lastNames[Math.floor(Math.random() * lastNames.length)];
        const registrationDate = randomDate(twoYearsAgo, today);

        // Create varied customer patterns
        let totalPurchases, totalSpent, lastPurchaseDate, purchaseFrequency;
        const customerType = Math.random();

        if (customerType < 0.15) {
            // Champions - frequent, recent, high value
            totalPurchases = Math.floor(Math.random() * 30) + 20; // 20-50
            totalSpent = Math.floor(Math.random() * 150000) + 100000; // ₹100k-250k
            lastPurchaseDate = randomDate(new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000), today);
            purchaseFrequency = Math.floor(Math.random() * 10) + 5; // 5-15 days
        } else if (customerType < 0.30) {
            // Loyal - frequent, recent, medium-high value
            totalPurchases = Math.floor(Math.random() * 20) + 10; // 10-30
            totalSpent = Math.floor(Math.random() * 80000) + 50000; // ₹50k-130k
            lastPurchaseDate = randomDate(new Date(today.getTime() - 45 * 24 * 60 * 60 * 1000), today);
            purchaseFrequency = Math.floor(Math.random() * 15) + 10; // 10-25 days
        } else if (customerType < 0.45) {
            // Recent/Promising - recent but low frequency
            totalPurchases = Math.floor(Math.random() * 5) + 1; // 1-6
            totalSpent = Math.floor(Math.random() * 30000) + 5000; // ₹5k-35k
            lastPurchaseDate = randomDate(new Date(today.getTime() - 60 * 24 * 60 * 60 * 1000), today);
            purchaseFrequency = Math.floor(Math.random() * 30) + 20; // 20-50 days
        } else if (customerType < 0.60) {
            // Need Attention - moderate activity
            totalPurchases = Math.floor(Math.random() * 10) + 5; // 5-15
            totalSpent = Math.floor(Math.random() * 50000) + 20000; // ₹20k-70k
            lastPurchaseDate = randomDate(new Date(today.getTime() - 90 * 24 * 60 * 60 * 1000), new Date(today.getTime() - 60 * 24 * 60 * 60 * 1000));
            purchaseFrequency = Math.floor(Math.random() * 20) + 15; // 15-35 days
        } else if (customerType < 0.75) {
            // At Risk - was active, now dormant
            totalPurchases = Math.floor(Math.random() * 15) + 8; // 8-23
            totalSpent = Math.floor(Math.random() * 70000) + 40000; // ₹40k-110k
            lastPurchaseDate = randomDate(new Date(today.getTime() - 180 * 24 * 60 * 60 * 1000), new Date(today.getTime() - 120 * 24 * 60 * 60 * 1000));
            purchaseFrequency = Math.floor(Math.random() * 25) + 20; // 20-45 days
        } else {
            // Hibernating/Lost - inactive
            totalPurchases = Math.floor(Math.random() * 5) + 1; // 1-6
            totalSpent = Math.floor(Math.random() * 20000) + 3000; // ₹3k-23k
            lastPurchaseDate = randomDate(new Date(today.getTime() - 365 * 24 * 60 * 60 * 1000), new Date(today.getTime() - 180 * 24 * 60 * 60 * 1000));
            purchaseFrequency = Math.floor(Math.random() * 40) + 30; // 30-70 days
        }

        const averageOrderValue = Math.floor(totalSpent / totalPurchases);
        const age = Math.floor(Math.random() * 40) + 20; // 20-60
        const gender = genders[Math.floor(Math.random() * genders.length)];
        const location = cities[Math.floor(Math.random() * cities.length)];
        const preferredCategory = categories[Math.floor(Math.random() * categories.length)];

        customers.push({
            id: `CUST${String(i + 1).padStart(4, '0')}`,
            name: `${firstName} ${lastName}`,
            email: `${firstName.toLowerCase()}.${lastName.toLowerCase()}@example.com`,
            phone: `+91 ${Math.floor(Math.random() * 9000000000) + 1000000000}`,
            registrationDate: registrationDate.toISOString().split('T')[0],
            lastPurchaseDate: lastPurchaseDate.toISOString().split('T')[0],
            totalPurchases,
            totalSpent,
            averageOrderValue,
            purchaseFrequency,
            demographics: {
                age,
                gender,
                location,
                preferredCategory
            }
        });
    }

    return customers;
};

export const mockCustomers = generateCustomers(120);

export default mockCustomers;
