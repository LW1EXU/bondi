package ar.com.bondi

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper

class BondiDbHelper(context: Context) : SQLiteOpenHelper(context, DATABASE_NAME, null, DATABASE_VERSION) {

    companion object {
        const val DATABASE_NAME = "bondi_offline.db"
        const val DATABASE_VERSION = 1

        const val TABLE_FAVORITES = "favorites"
        const val COL_LINE_ID = "line_id"
        const val COL_CREATED_AT = "created_at"

        const val TABLE_SYNC_CACHE = "sync_cache"
        const val COL_CACHE_KEY = "cache_key"
        const val COL_CACHE_DATA = "cache_data"
        const val COL_UPDATED_AT = "updated_at"
    }

    override fun onCreate(db: SQLiteDatabase) {
        db.execSQL(
            """
            CREATE TABLE $TABLE_FAVORITES (
                $COL_LINE_ID TEXT PRIMARY KEY,
                $COL_CREATED_AT INTEGER NOT NULL
            )
            """.trimIndent()
        )

        db.execSQL(
            """
            CREATE TABLE $TABLE_SYNC_CACHE (
                $COL_CACHE_KEY TEXT PRIMARY KEY,
                $COL_CACHE_DATA TEXT NOT NULL,
                $COL_UPDATED_AT INTEGER NOT NULL
            )
            """.trimIndent()
        )
    }

    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) {
        db.execSQL("DROP TABLE IF EXISTS $TABLE_FAVORITES")
        db.execSQL("DROP TABLE IF EXISTS $TABLE_SYNC_CACHE")
        onCreate(db)
    }

    fun getFavorites(): Set<String> {
        val result = mutableSetOf<String>()
        readableDatabase.query(
            TABLE_FAVORITES,
            arrayOf(COL_LINE_ID),
            null,
            null,
            null,
            null,
            null
        ).use { cursor ->
            val idx = cursor.getColumnIndexOrThrow(COL_LINE_ID)
            while (cursor.moveToNext()) {
                result.add(cursor.getString(idx))
            }
        }
        return result
    }

    fun setFavorite(lineId: String, isFavorite: Boolean) {
        writableDatabase.let { db ->
            if (isFavorite) {
                val cv = ContentValues().apply {
                    put(COL_LINE_ID, lineId)
                    put(COL_CREATED_AT, System.currentTimeMillis())
                }
                db.insertWithOnConflict(TABLE_FAVORITES, null, cv, SQLiteDatabase.CONFLICT_REPLACE)
            } else {
                db.delete(TABLE_FAVORITES, "$COL_LINE_ID = ?", arrayOf(lineId))
            }
        }
    }
}
