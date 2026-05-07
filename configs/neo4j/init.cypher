// Neo4j Initialization Cypher
// Run this after Neo4j starts to set up schema

// ============================================================
// Constraints (unique identifiers)
// ============================================================
CREATE CONSTRAINT menu_item_id IF NOT EXISTS FOR (m:MenuItem) REQUIRE m.id IS UNIQUE;
CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE;
CREATE CONSTRAINT category_name IF NOT EXISTS FOR (cat:Category) REQUIRE cat.name IS UNIQUE;

// ============================================================
// Indexes (search performance)
// ============================================================
CREATE INDEX menu_item_name IF NOT EXISTS FOR (m:MenuItem) ON (m.name);
CREATE INDEX menu_item_category IF NOT EXISTS FOR (m:MenuItem) ON (m.category);
CREATE INDEX chunk_source IF NOT EXISTS FOR (c:Chunk) ON (c.source);
CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type);
