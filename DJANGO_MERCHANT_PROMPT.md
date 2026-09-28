# Complete Django E-Commerce Auction System - Comprehensive Development Prompt

## Project Overview
Build a complete Django-based e-commerce auction platform that replicates ALL functionality from the existing PHP system. This is a production-ready system with advanced auction mechanics, multi-user roles, and complex business logic.

## Core Requirements - NO SHORTCUTS

### 1. User Management System
- **User Roles**: Buyer, Seller, Admin, Rider (using Django's custom user model or role-based permissions)
- **Default Role**: All users start as buyers by default
- **Seller Mode Toggle**: Users can enable seller mode (seller_enabled field) to become sellers
- **User Profiles**: Separate profile models for each role (SellerProfile, BuyerProfile, RiderProfile)
- **Authentication**: Django Auth system with email-based login, password reset functionality
- **User Status**: Active, Suspended, Pending
- **Seller Verification**: Business name, address, verification status, ratings
- **Email Verification**: Email verification system for new users

### 2. Category & Size System
- **Cascading Categories**: Main categories → Item types → Sub types with parent-child relationships
- **Category Types**: main, item_type, sub_type
- **Size Systems**: Alpha sizing, numeric waist/length, chest sizing, shoe sizing (US/EU/UK), none
- **Size Specifications**: Dynamic size values per category with sort order
- **Category Attributes**: Custom attributes per category (select, text, etc.)
- **Attribute Values**: Predefined values for select-type attributes
- **Listing Attributes**: User-defined attribute values for specific listings

### 3. Listing Management System
- **Listing Types**: Auction, Buy Now, Both (combined auction + buy now)
- **Listing Status**: Draft, Active, Ended, Sold, Cancelled, Relisted
- **Condition Types**: New, Like New, Good, Fair, For Parts
- **Pricing Fields**: Starting bid, current bid, buy now price, reserve price, display price, minimum increment
- **Auction Management**: Auction start/end times, anti-snipe seconds, auto-relist functionality
- **Quantity Management**: Critical field structure:
  - `quantity`: Total original quantity
  - `available_stock`: Available for buy-now purchases
  - `auction_quantity`: Quantity allocated to auction
  - `quantity_sold`: Total quantity sold (both buy-now and auction)
  - Inventory logic: When auctioning from buy-now, reduces available_stock and creates auction listing
- **Image Management**: Multiple images per listing with primary image designation, sort order, alt text
- **Slug Generation**: Auto-generated unique slugs for SEO-friendly URLs
- **View Tracking**: Track listing views by users and IP addresses
- **Original Listing Tracking**: Track relisted items back to originals
- **Inventory Source Tracking**: Track which buy-now listing an auction was created from

### 4. Advanced Bidding System (CRITICAL - Most Complex)
- **Regular Bids**: Standard bid placement with amount, timestamp, auto-bid flag
- **Bid Status System**: Active, Outbid, Winning, Won, Cancelled, Pending Cancel
- **Max Bid Caps (Proxy Bidding)**: Users set maximum bid amounts, system auto-bids on their behalf
- **Automatic Increment Logic**: CRITICAL - When buyer sets max bid, system automatically increments bids as other users bid
  - Example: Buyer sets max bid of $100, current bid is $50
  - Another user bids $60, system automatically bids $61 for the max-bid user
  - System continues to auto-bid up to the max bid cap
  - Buyer gets notification each time their auto-bid is triggered
- **Personal Bidder Increments**: Users can set preferred bid increments per listing
- **Anti-Snipe Protection**: Extend auction end time if bids placed in final seconds
- **Reserve Price Logic**: Track reserve price meeting status, handle reserve-not-met scenarios
- **Minimum Increment Enforcement**: Enforce minimum bid increments between bids
- **Bid Cancellation Requests**: System for users to request bid cancellations with admin review ONLY
- **Admin Cancellation Management**: Admin exclusively manages bid cancellation requests (approve/deny)
- **Highest Bidder Cancellation Flow**: CRITICAL - When highest bidder cancels:
  1. System automatically offers item to second-highest bidder at their bid amount
  2. Second-highest bidder can accept or decline
  3. If accepted: Creates order and completes sale
  4. If declined: Item goes to relist status
  5. Seller gets one-tap option to re-auction the item
  6. Seller can choose to re-auction immediately or schedule for later
- **Auction Extensions**: Track anti-snipe extensions with previous/new end times
- **Winning Bid Management**: Track current winning bid and winning bidder
- **Automatic Bid Processing**: Background tasks to process max bid caps and auto-bidding
- **Second Chance Offers**: When highest bidder doesn't meet reserve, offer to second-highest bidder

### 5. Second Chance Offer System
- **Trigger Conditions**: Automatically trigger when auction ends with reserve not met
- **Offer Generation**: Create offers for second-highest bidder at their bid amount
- **Offer Status**: Pending, Accepted, Declined, Expired
- **Expiration**: Offers expire after set time period
- **Notification**: Notify eligible buyers of second chance offers

### 6. Order Management System
- **Order Creation**: From buy-now purchases, auction wins, second chance offers
- **Order Status Workflow**: Pending → Paid → Processing → Rider Assigned → Rider Accepted → Picked Up → In Transit → Shipped → Delivered → Cancelled/Disputed
- **Payment Methods**: Online payment, Cash on Delivery (COD)
- **Escrow System**: Hold funds in escrow until delivery confirmation
- **Shipping Management**: Shipping addresses, tracking numbers, carrier information
- **Rider Assignment**: Assign delivery riders to orders
- **Order Number Generation**: Unique order numbers for reference

### 7. Rider Delivery System
- **Rider Availability**: Real-time availability status
- **Location Tracking**: GPS location tracking for riders
- **Vehicle Information**: Vehicle type, plate number
- **Delivery Statistics**: Rating average, total deliveries
- **Order Assignment**: Order-to-rider matching system
- **Delivery Updates**: Real-time delivery status updates

### 8. Wallet & Payment System
- **User Wallets**: Balance tracking for each user
- **Transaction Types**: Deposits, withdrawals, payments, refunds, escrow holds/releases
- **Transaction History**: Complete audit trail of all wallet transactions
- **Balance Tracking**: Real-time balance updates after each transaction

### 9. Notification System
- **Notification Types**: Outbid notifications, bid status updates, price drops, saved search matches, order updates, chat messages
- **Notification Channels**: In-app, email, push notifications
- **Notification Preferences**: User-configurable preferences per notification type
- **Read Status**: Track read/unread status for notifications
- **Real-time Events**: Real-time event streaming for live auction updates

### 10. Chat & Messaging System
- **Conversations**: Between buyers and sellers, linked to specific listings
- **Message Storage**: Complete message history with read status
- **Real-time Messaging**: Real-time chat functionality (WebSockets/Django Channels)
- **Conversation Management**: Unique conversations per listing-buyer-seller combination

### 11. Wishlist & Saved Searches
- **Wishlist as Add-to-Cart**: Wishlist functions like an add-to-cart system
  - Users can add multiple items to wishlist
  - Wishlist shows item details, prices, availability
  - Users can proceed to checkout from wishlist (for buy-now items)
  - For auction items, wishlist shows auction status and current bid
  - Wishlist persists across sessions
- **Wishlist Notifications**: Notify users of price drops and inventory changes
- **Saved Searches**: Users can save search criteria
- **Search Matching**: Auto-match new listings against saved searches
- **Search Notifications**: Notify users when new listings match their saved searches

### 12. Inventory Management
- **Inventory Logs**: Track all inventory changes (restock, sale, adjustment, return, relist)
- **Quantity Tracking**: Before/after quantities for each change
- **Change Types**: Different types of inventory changes with appropriate tracking
- **Inventory Analytics**: Demand forecasting based on sales history
- **Inventory-to-Auction Conversion**: Critical behavior - when auctioning from buy-now inventory:
  - System automatically creates separate auction listing from existing buy-now listing
  - Reduces available stock of original buy-now listing by auctioned quantity
  - Example: If user has 10 buy-now items and auctions 1:
    - Original buy-now listing: 9 remaining available stock
    - New auction listing: 1 auction quantity created
  - Preserves all original listing data (images, attributes, description)
  - Links auction listing back to original inventory source
- **Stock Management**: Real-time stock tracking across all listing types
- **Inventory Deduction**: Automatic stock deduction on sales and auction wins

### 13. Price Comparison & Analytics
- **Price Snapshots**: Track price history for listings
- **Comparable Listings**: Price comparison with similar listings
- **Category Price Statistics**: Min/avg/max prices per category
- **Sales History**: Complete sales tracking with prices and quantities
- **Demand Forecasting**: Predict future demand based on historical data

### 14. Relisting System
- **One-Click Relisting**: Quick relist of ended auctions
- **Scheduled Relisting**: Schedule automatic relisting for specific times
- **Relist Modes**: Different relisting strategies
- **Relist Jobs**: Track relisting operations with status
- **Original Tracking**: Maintain link to original listings

### 15. Admin & Moderation
- **User Management**: Admin can manage users, suspend accounts
- **Bid Cancellation Review**: Admin review system for bid cancellation requests
- **Content Moderation**: Admin can moderate listings, images, messages
- **System Analytics**: Admin dashboard with system statistics

## Technical Requirements

### Database Design
- **Database**: PostgreSQL (exact replica of existing schema)
- **ORM**: Django ORM with proper model relationships
- **All Tables Must Include**:
  - Users (with seller_enabled field - default False), seller_profiles, buyer_profiles, password_resets, sessions
  - Categories, size_specifications, category_attributes, attribute_values, listing_attributes
  - Listings (with quantity, available_stock, auction_quantity, quantity_sold fields), listing_images
  - Bids, max_bid_caps, bid_cancellation_requests, auction_extensions
  - Wishlists, saved_searches
  - Notifications, notification_preferences
  - Conversations, chat_messages
  - Price_snapshots, category_price_stats, realtime_events
  - Inventory_logs, listing_views, sales_history, demand_forecasts
  - Relisting_jobs
  - Orders, wallets, wallet_transactions
  - Riders, rider_locations
  - Second_chance_offers

### Key Django Features to Implement
- **Signals**: For automated actions (notifications, status updates, etc.)
- **Background Tasks**: Celery/Redis for async processing (auction endings, notifications)
- **Caching**: Redis for performance optimization
- **API**: Django REST Framework for mobile app integration
- **Real-time**: Django Channels for WebSocket functionality
- **Admin Panel**: Custom Django admin with all models
- **Testing**: Comprehensive test coverage for all business logic

### Business Logic Requirements
- **Atomic Operations**: All bid placements must be atomic with database locks
- **Transaction Management**: Proper transaction handling for complex operations
- **Data Validation**: Comprehensive validation at model and form levels
- **Error Handling**: Robust error handling and user feedback
- **Audit Trail**: Complete audit logging for critical operations
- **User Role Management**: All users start as buyers (seller_enabled=False), can toggle seller mode
- **Inventory Conversion Logic**: Critical atomic operation for buy-now to auction conversion
- **Quantity Synchronization**: Ensure quantities stay synchronized across listing types
- **Stock Deduction**: Automatic stock updates on sales, auction wins, and conversions

### Deployment Requirements
- **Platform**: Render.com
- **Database**: Render PostgreSQL
- **Redis**: Render Redis for caching and Celery
- **Static Files**: Whitenoise for static file serving
- **Environment Variables**: All configuration via environment variables
- **Migration System**: Django migrations for database schema management
- **Zero Downtime**: Proper deployment with zero downtime

## Specific Complex Logic to Implement

### Bid Placement Algorithm
1. Lock listing row for update
2. Validate auction status, timing, user permissions
3. Calculate minimum next bid (current + increment)
4. Check against user's max bid cap (if set)
5. Process proxy bidding if another bidder's cap is exceeded
6. Handle anti-snipe timer extension
7. Update bid statuses (mark others as outbid)
8. Update listing current bid, display price, reserve status
9. Create notifications for outbid users
10. Record auction extension if anti-snipe triggered

### Second Chance Offer Logic
1. Check if auction ended with reserve not met
2. Identify second-highest bidder
3. Create second chance offer at their bid amount
4. Set expiration time
5. Send notification to eligible buyer
6. Handle acceptance/decline responses
7. Create order if accepted

### Auto-Relist Logic
1. Check for ended auctions with auto_relist enabled
2. Clone listing with new auction dates
3. Copy images and attributes
4. Mark original as relisted
5. Create relisting job record
6. Send notifications to watchers

### Inventory-to-Auction Conversion Logic (CRITICAL)
1. User selects buy-now listing to auction from inventory
2. User specifies quantity to auction (e.g., 1 from 10 available)
3. System creates NEW auction listing with:
   - Copied title, description, images, attributes from original
   - auction_quantity = specified quantity (e.g., 1)
   - available_stock = 0 (auction-only)
   - auction pricing (starting bid, reserve, etc.)
4. System updates ORIGINAL buy-now listing:
   - Reduces available_stock by auctioned quantity (e.g., 10 → 9)
   - Keeps all other data unchanged
5. Links auction listing to original via original_listing_id or custom field
6. Tracks inventory log for the conversion
7. Example scenario:
   - Original: "iPhone 13" - Buy Now - 10 available - $699
   - User auctions 1 item
   - Original: "iPhone 13" - Buy Now - 9 available - $699
   - New: "iPhone 13" - Auction - 1 auction qty - starting bid $500
8. This preserves inventory integrity while enabling flexible auction creation

### Max Bid Cap Processing
1. Find all active max bid caps for active auctions
2. For each cap, check if current bid is below cap
3. Auto-bid minimum increment if beneficial
4. Handle multiple competing caps
5. Respect personal bidder increments
6. Update bid statuses accordingly

### Highest Bidder Cancellation Flow (CRITICAL - Complete Workflow)
1. **Cancellation Request**: User requests bid cancellation OR system generates cancellation (e.g., account suspension)
2. **Admin Review**: Admin exclusively reviews cancellation requests in dedicated admin panel
3. **Admin Decision**: Admin can approve or deny cancellation with notes
4. **If Cancelled Highest Bidder**:
   - System automatically identifies second-highest bidder
   - System creates automatic offer to second-highest bidder at their bid amount
   - Second-highest bidder receives notification with accept/decline options
   - **If Accepted**: Create order, process payment, complete sale
   - **If Declined**: Item status changes to "pending_relist"
   - Seller receives notification that item is available for re-auction
   - Seller gets one-tap "Re-Auction Now" button in dashboard
   - Seller can also choose "Schedule Re-Auction" for specific time
   - System creates new auction listing with original data
   - Original listing marked as "relisted"
5. **If Cancelled Non-Highest Bidder**: Simply remove bid, no second chance offer needed
6. **Audit Trail**: Complete log of all cancellation decisions and actions

## UI/UX Requirements
- **Responsive Design**: Mobile-first responsive design
- **Real-time Updates**: Live bid updates, countdown timers
- **User Dashboard**: Separate dashboards for buyers, sellers, admins, riders
- **Seller Mode Toggle**: Clear UI option for buyers to enable seller mode
- **Seller Activation Process**: Step-by-step seller profile setup when enabling seller mode
- **Inventory Management Interface**: View all buy-now inventory with stock levels
- **Auction Creation Interface**: Select buy-now items to convert to auctions
- **Quantity Selection UI**: Choose how many items to auction from inventory
- **Stock Visualization**: Clear display of quantity changes (10 → 9 buy-now + 1 auction)
- **Bid Overview Interface**: CRITICAL - Complete bidding interface with:
  - Current highest bid display
  - Your current bid status (winning, outbid, etc.)
  - Your max bid cap setting
  - Bid history with timestamps and bidder info
  - Automatic increment status display
  - Time remaining countdown
  - Minimum next bid calculation
  - Quick bid buttons (min increment, custom amount)
  - Max bid cap input with auto-bid toggle
  - Real-time bid updates via WebSocket
- **Wishlist/Cart Interface**: Add-to-cart functionality from wishlist
- **Search & Filter**: Advanced search with category, price, condition filters
- **Image Management**: Image upload with drag-and-drop, primary image selection
- **Forms**: Comprehensive forms with validation and user feedback

## Security Requirements
- **CSRF Protection**: Django's built-in CSRF protection
- **SQL Injection Prevention**: Parameterized queries via Django ORM
- **XSS Protection**: Django's built-in XSS protection
- **Authentication Security**: Secure password hashing, session management
- **Authorization**: Role-based access control
- **Rate Limiting**: API rate limiting
- **Input Validation**: Comprehensive input validation and sanitization

## Performance Requirements
- **Database Optimization**: Proper indexing, query optimization
- **Caching Strategy**: Redis caching for frequently accessed data
- **Async Processing**: Background tasks for time-consuming operations
- **Database Connection Pooling**: Efficient connection management
- **Static Asset Optimization**: Minification, compression, CDN

## Testing Requirements
- **Unit Tests**: Test all business logic functions
- **Integration Tests**: Test complete user flows
- **Model Tests**: Test all model methods and validations
- **API Tests**: Test all API endpoints
- **Performance Tests**: Load testing for critical paths
- **Critical Business Logic Tests**:
  - Test user starts as buyer, can enable seller mode
  - Test seller mode toggle functionality and permissions
  - Test inventory-to-auction conversion (10 buy-now → 9 buy-now + 1 auction)
  - Test quantity tracking across listing types
  - Test stock deduction on sales and auction wins
  - Test that auction creation properly reduces original inventory
  - Test that auction listing preserves all original data

## Documentation Requirements
- **API Documentation**: Complete API documentation with examples
- **User Documentation**: User guides for each role
- **Admin Documentation**: Admin operation guides
- **Deployment Documentation**: Step-by-step deployment guide
- **Code Documentation**: Comprehensive code comments and docstrings

## Migration Requirements
- **Data Migration Script**: Script to migrate existing PostgreSQL data to Django models
- **Image Migration**: Migrate existing images to Django's file storage
- **User Migration**: Migrate users with password hashes (compatible with Django)
- **Seller Mode Migration**: Migrate seller_enabled field and user roles
- **Inventory Migration**: Migrate inventory data with proper quantity fields
- **Listing Migration**: Migrate listings with quantity tracking (quantity, available_stock, auction_quantity, quantity_sold)
- **Settings Migration**: Migrate configuration settings

## Success Criteria
- **Complete Feature Parity**: All features from PHP system must be present
- **No Data Loss**: Complete data migration from existing system
- **Improved Performance**: Better performance than PHP system
- **Enhanced Security**: Security improvements over PHP system
- **Scalability**: System must handle growth in users and listings
- **Maintainability**: Clean, well-documented, maintainable code
- **Zero Bugs**: No critical bugs in production
- **Phase 3 Deployment**: Phase 3 must be fully deployable to Render for testing

## Phase 1: Core Foundation (Local Development)
- Django project setup with PostgreSQL
- User authentication and authorization
- User model with seller_enabled field (default False)
- Seller mode toggle functionality
- Basic user models and profiles (SellerProfile, BuyerProfile)
- Category and size system
- Basic listing CRUD operations
- Inventory management interface

## Phase 2: Basic Bidding System (Local Development)
- Bid placement logic with minimum increments
- Max bid cap system with automatic increment logic
- Basic bid status management
- Bid overview interface
- Real-time bid updates (basic WebSocket)
- Anti-snipe protection (basic)

## Phase 3: Core Marketplace with Render Deployment (TESTABLE DEPLOYMENT)
- **CRITICAL: This phase must be deployable to Render for testing**
- Complete bidding system with automatic increments
- Order creation and management (basic)
- Basic payment processing (mock)
- **Inventory-to-Auction Conversion**: Buy-now to auction conversion logic
- **Quantity Management**: Stock tracking across listing types
- Wishlist with add-to-cart functionality
- Basic notifications (in-app only)
- **Render Deployment**: Full deployment to Render.com
- **Database Setup**: PostgreSQL on Render
- **Testing Environment**: Deployed system ready for user testing
- **Test Coverage**: All phase 1-3 functionality tested
- **Performance**: Basic optimization for Render deployment

## Phase 4: Advanced Features (Post-Testing)
- Second chance offers with automatic flow
- Auto-relist functionality with one-tap relist
- Complete notification system (email, push, in-app)
- Chat system with real-time messaging
- Advanced saved searches and matching

## Phase 5: Payment & Delivery System (Post-Testing)
- Complete payment processing integration
- Escrow system with hold/release
- Rider system with GPS tracking
- Delivery management
- Wallet system with transactions

## Phase 6: Analytics & Admin (Post-Testing)
- Price comparison analytics
- Sales analytics and forecasting
- Complete admin dashboard
- Admin cancellation management system
- User management and moderation
- System monitoring and logging

## Phase 7: Production Migration & Launch (Final)
- Data migration from existing PHP system
- Image migration
- User migration with password compatibility
- Performance optimization
- Security hardening
- Production launch
- Zero-downtime deployment

## Important Notes
- **NO SHORTCUTS**: Every feature must be implemented completely
- **NO MISSING FUNCTIONALITY**: If it exists in the PHP system, it must exist here
- **PRODUCTION QUALITY**: This must be production-ready code
- **SCALABLE ARCHITECTURE**: Design for growth and scalability
- **COMPREHENSIVE TESTING**: Test everything thoroughly
- **COMPLETE DOCUMENTATION**: Document everything extensively

This is a complex, production-grade e-commerce auction system. Do not underestimate the complexity. Take the time to understand each requirement before implementation. Quality and completeness are more important than speed.