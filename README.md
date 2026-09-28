# Django Merchant - E-Commerce Auction System

A complete Django-based e-commerce auction platform with advanced bidding mechanics, multi-user roles, and complex business logic.

## Project Overview

This is a production-ready Django system that replicates all functionality from the previous PHP system, but with improved deployment reliability and modern architecture.

## Key Features

- **User Management**: Buyer, Seller, Admin, Rider roles with seller mode toggle
- **Advanced Bidding**: Max bid caps, automatic increments, anti-snipe protection
- **Inventory Management**: Buy-now to auction conversion with quantity tracking
- **Order System**: Complete order workflow with escrow and delivery tracking
- **Real-time Features**: Live bidding, notifications, chat via WebSockets
- **Second Chance Offers**: Automatic offers to second-highest bidders

## Tech Stack

- **Backend**: Django 4.x with Python 3.11+
- **Database**: PostgreSQL
- **Caching/Queue**: Redis
- **Real-time**: Django Channels (WebSockets)
- **Background Tasks**: Celery
- **Deployment**: Render.com

## Development Phases

1. **Phase 1**: Core Foundation (auth, users, categories, listings)
2. **Phase 2**: Basic Bidding System (bid placement, max caps, real-time)
3. **Phase 3**: Core Marketplace + Render Deployment (TESTABLE)
4. **Phase 4**: Advanced Features (second chance, notifications, chat)
5. **Phase 5**: Payment & Delivery System
6. **Phase 6**: Analytics & Admin
7. **Phase 7**: Production Migration & Launch

## Current Status

- 📝 Project initialization
- 🔄 Setting up online development environment
- 🎯 Target: Phase 3 deployment to Render for testing

## Development Approach

This project is developed entirely online with git integration to ensure:
- Continuous deployment readiness
- No local environment issues
- Immediate testing on Render
- Version control for all changes

## Documentation

See `DJANGO_MERCHANT_PROMPT.md` for complete technical specifications and requirements.