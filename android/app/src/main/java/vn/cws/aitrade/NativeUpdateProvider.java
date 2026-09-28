package vn.cws.aitrade;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.database.Cursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;

import java.io.File;
import java.io.FileNotFoundException;

/** Grants the system installer read-only access to one verified staged APK. */
public final class NativeUpdateProvider extends ContentProvider {
    public static final String AUTHORITY = "vn.cws.aitrade.release";
    public static final String PATH = "/cws-update.apk";
    public static final String MIME = "application/vnd.android.package-archive";

    @Override public boolean onCreate() { return true; }
    @Override public String getType(Uri uri) { return valid(uri) ? MIME : null; }

    @Override public ParcelFileDescriptor openFile(Uri uri, String mode)
        throws FileNotFoundException {
        if (!valid(uri) || !"r".equals(mode) || getContext() == null) {
            throw new FileNotFoundException("Invalid update URI or mode");
        }
        File base = new File(getContext().getCacheDir(), "cws_updates");
        File verified = new File(base, "cws-update.apk");
        if (!verified.isFile()) throw new FileNotFoundException("No staged update");
        return ParcelFileDescriptor.open(verified, ParcelFileDescriptor.MODE_READ_ONLY);
    }

    private static boolean valid(Uri uri) {
        return uri != null && "content".equals(uri.getScheme())
            && AUTHORITY.equals(uri.getAuthority()) && PATH.equals(uri.getPath())
            && uri.getQuery() == null && uri.getFragment() == null;
    }
    @Override public Cursor query(Uri uri, String[] projection, String selection,
                                  String[] selectionArgs, String sortOrder) {
        return null;
    }
    @Override public Uri insert(Uri uri, ContentValues values) {
        throw new SecurityException("Update provider is read only");
    }
    @Override public int delete(Uri uri, String selection, String[] selectionArgs) {
        throw new SecurityException("Update provider is read only");
    }
    @Override public int update(Uri uri, ContentValues values, String selection,
                                String[] selectionArgs) {
        throw new SecurityException("Update provider is read only");
    }
}
