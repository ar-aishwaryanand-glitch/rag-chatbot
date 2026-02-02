# Product API Documentation

## Overview

The Product API allows you to manage products in your inventory system. This RESTful API supports CRUD operations and uses JSON for request and response payloads.

## Base URL

```
https://api.example.com/v1
```

## Authentication

All API requests require authentication using an API key. Include your API key in the request header:

```
Authorization: Bearer YOUR_API_KEY
```

To obtain an API key, visit your dashboard at https://dashboard.example.com/api-keys

## Endpoints

### List Products

Retrieve a list of all products.

**Endpoint:** `GET /products`

**Query Parameters:**
- `page` (optional): Page number for pagination (default: 1)
- `limit` (optional): Number of items per page (default: 20, max: 100)
- `category` (optional): Filter by product category
- `status` (optional): Filter by status (active, inactive, draft)

**Example Request:**
```bash
curl -X GET "https://api.example.com/v1/products?page=1&limit=20" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Example Response:**
```json
{
  "data": [
    {
      "id": "prod_123",
      "name": "Wireless Headphones",
      "description": "Premium noise-cancelling headphones",
      "price": 299.99,
      "category": "electronics",
      "status": "active",
      "stock": 150,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 5,
    "total_items": 87
  }
}
```

### Get Product

Retrieve details of a specific product.

**Endpoint:** `GET /products/{product_id}`

**Example Request:**
```bash
curl -X GET "https://api.example.com/v1/products/prod_123" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Create Product

Create a new product.

**Endpoint:** `POST /products`

**Request Body:**
```json
{
  "name": "Product Name",
  "description": "Product description",
  "price": 99.99,
  "category": "electronics",
  "stock": 100
}
```

**Example Request:**
```bash
curl -X POST "https://api.example.com/v1/products" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Wireless Mouse",
    "description": "Ergonomic wireless mouse",
    "price": 49.99,
    "category": "electronics",
    "stock": 200
  }'
```

### Update Product

Update an existing product.

**Endpoint:** `PUT /products/{product_id}`

**Request Body:** (same as Create Product)

### Delete Product

Delete a product.

**Endpoint:** `DELETE /products/{product_id}`

## Rate Limits

- 1000 requests per hour for authenticated users
- 100 requests per hour for unauthenticated users
- Rate limit headers included in all responses

## Error Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Invalid or missing API key
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Support

For API support, contact: api-support@example.com
