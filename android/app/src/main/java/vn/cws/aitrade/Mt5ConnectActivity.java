package vn.cws.aitrade;

import android.app.Activity;
import android.os.Bundle;
import android.text.InputType;
import android.view.WindowManager;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Spinner;
import android.widget.TextView;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public final class Mt5ConnectActivity extends Activity {
    private final ExecutorService network=Executors.newSingleThreadExecutor();
    private EditText login,password;
    private Spinner brokerSpinner;
    private final List<NativeMt5BrokerOption> brokerOptions=new ArrayList<>();
    private ArrayAdapter<NativeMt5BrokerOption> brokerAdapter;
    private CheckBox remember,showPassword;
    private Button connect,disconnect,autoTrade;
    private TextView status,account;
    private volatile String sessionId="";
    private NativeMt5EncryptedSession encryptedSession;
    private volatile long generation=0L;

    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        encryptedSession=new NativeMt5EncryptedSession(this);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
        LinearLayout form=new LinearLayout(this);
        form.setOrientation(LinearLayout.VERTICAL);
        form.setPadding(22,22,22,22);
        TextView title=new TextView(this);
        title.setText("CWS AutoTrade | MT5 DEMO");
        title.setTextSize(22);
        form.addView(title);
        status=new TextView(this);
        status.setText(bridgeConfigured() ? "Chưa kết nối. AutoTrade: OFF. DEMO only." : "MT5 Bridge chưa cấu hình. AutoTrade: OFF.");
        form.addView(status);

        TextView brokerLabel=new TextView(this);
        brokerLabel.setText("Broker / MT5 Server");
        form.addView(brokerLabel);
        brokerSpinner=new Spinner(this);
        brokerAdapter=new ArrayAdapter<>(this,
            android.R.layout.simple_spinner_item,brokerOptions);
        brokerAdapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        brokerSpinner.setAdapter(brokerAdapter);
        form.addView(brokerSpinner);
        seedBrokerCatalog();

        login=input(form,"Login / Account Number",InputType.TYPE_CLASS_NUMBER);
        password=input(form,"Password",InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_PASSWORD);

        showPassword=new CheckBox(this);
        showPassword.setText("Hiện mật khẩu");
        showPassword.setOnCheckedChangeListener((button,checked)->{
            int pos=password.getSelectionStart();
            password.setInputType(InputType.TYPE_CLASS_TEXT | (checked ? InputType.TYPE_TEXT_VARIATION_VISIBLE_PASSWORD : InputType.TYPE_TEXT_VARIATION_PASSWORD));
            if(pos>=0 && pos<=password.length()) password.setSelection(pos);
        });
        form.addView(showPassword);

        remember=new CheckBox(this);
        remember.setText("Tự động ghi nhớ đăng nhập (mã hóa)");
        remember.setChecked(true);
        remember.setEnabled(false);
        form.addView(remember);

        connect=new Button(this);
        connect.setText("KẾT NỐI MT5");
        connect.setEnabled(bridgeConfigured());
        connect.setOnClickListener(v->connect());
        form.addView(connect);

        disconnect=new Button(this);
        disconnect.setText("Disconnect");
        disconnect.setEnabled(false);
        disconnect.setOnClickListener(v->disconnect());
        form.addView(disconnect);

        autoTrade=new Button(this);
        autoTrade.setText("BẬT AUTOTRADE DEMO");
        autoTrade.setEnabled(false);
        autoTrade.setOnClickListener(v->{
            status.setText("AUTOTRADE_BLOCKED: chưa có execution provider DEMO được phê duyệt.");
        });
        form.addView(autoTrade);

        account=new TextView(this);
        account.setText("Disconnected\nDEMO\nBalance: —\nEquity: —\nAutoTrade: OFF");
        form.addView(account);

        ScrollView scroll=new ScrollView(this);
        scroll.addView(form);
        setContentView(scroll);
        refreshBrokerCatalog();
        restoreSession();
    }


    private void seedBrokerCatalog(){
        brokerOptions.clear();
        brokerOptions.add(new NativeMt5BrokerOption("MetaQuotes Ltd.","MetaQuotes-Demo"));
        if(brokerAdapter!=null) brokerAdapter.notifyDataSetChanged();
    }

    private void refreshBrokerCatalog(){
        network.execute(()->{
            try{
                JSONObject reply=request("GET","/mt5/brokers",null,null,15000);
                JSONArray brokers=reply.optJSONArray("brokers");
                if(brokers==null) throw new IOException("BROKER_CATALOG_INVALID");
                ArrayList<NativeMt5BrokerOption> fresh=new ArrayList<>();
                for(int i=0;i<brokers.length();i++){
                    JSONObject broker=brokers.optJSONObject(i);
                    if(broker==null) continue;
                    String name=broker.optString("name","").trim();
                    JSONArray servers=broker.optJSONArray("servers");
                    if(name.isEmpty()||servers==null) continue;
                    for(int j=0;j<servers.length();j++){
                        JSONObject item=servers.optJSONObject(j);
                        if(item==null||!item.optBoolean("supported",false)) continue;
                        String host=item.optString("server","").trim();
                        String mode=item.optString("mode","");
                        if(!"DEMO".equals(mode)||!NativeMt5SessionContract.validServer(host)) continue;
                        fresh.add(new NativeMt5BrokerOption(name,host));
                    }
                }
                if(fresh.isEmpty()) throw new IOException("BROKER_CATALOG_EMPTY");
                runOnUiThread(()->{
                    brokerOptions.clear();
                    brokerOptions.addAll(fresh);
                    brokerAdapter.notifyDataSetChanged();
                });
            }catch(Exception ignored){
                // Keep the bundled catalog. Never replace it with unverified entries.
            }
        });
    }

    private EditText input(LinearLayout form,String hint,int type){
        EditText out=new EditText(this);
        out.setHint(hint);
        out.setInputType(type);
        out.setSingleLine(true);
        form.addView(out);
        return out;
    }

    private static boolean bridgeConfigured(){
        return BuildConfig.CWS_MT5_BRIDGE_BASE_URL!=null
            && BuildConfig.CWS_MT5_BRIDGE_BASE_URL.startsWith("https://")
            && !BuildConfig.CWS_MT5_BRIDGE_BASE_URL.endsWith("/");
    }

    private void connect(){
        final long op=++generation;
        final NativeMt5BrokerOption selected=(NativeMt5BrokerOption)brokerSpinner.getSelectedItem();
        final String host=selected==null?"":selected.server;
        final String accountLogin=login.getText().toString().trim();
        final String secret=password.getText().toString();
        final boolean persist=true;
        final String previousSession=sessionId;
        sessionId="";
        try{ encryptedSession.clear(); }catch(Exception ignored){ }
        password.setText("");
        if(!NativeMt5SessionContract.validServer(host)
            || !NativeMt5SessionContract.validLogin(accountLogin)
            || !NativeMt5SessionContract.validPassword(secret)){
            status.setText("Thông tin kết nối không hợp lệ. AutoTrade: OFF.");
            return;
        }
        connect.setEnabled(false);
        disconnect.setEnabled(false);
        status.setText("Đang kết nối MT5 DEMO…");
        network.execute(()->{
            try{
                JSONObject body=new JSONObject();
                body.put("server",host);
                body.put("login",Long.parseLong(accountLogin));
                body.put("password",secret);
                body.put("remember",persist);
                if(!previousSession.isEmpty()){
                    try{ request("POST","/mt5/session/disconnect",null,previousSession,15000); }
                    catch(Exception ignored){ }
                }
                JSONObject reply=request("POST","/mt5/session/connect",body,null,125000);
                if(op!=generation) return;
                validateConnected(reply,host,accountLogin);
                String token=reply.getString("session_id");
                try{
                    encryptedSession.save(token);
                }catch(Exception storageError){
                    try{ request("POST","/mt5/session/disconnect",null,token,15000); }
                    catch(Exception ignored){ }
                    throw new IOException("LOCAL_SESSION_STORE_FAILED");
                }
                JSONObject info=reply.getJSONObject("account");
                final String state=reply.getString("status");
                final String display=("CONNECTED_READ_ONLY".equals(state)?"Read-only":"Connected")
                    +"\nServer: "+info.getString("server")
                    +"\nAccount: "+NativeMt5SessionContract.maskLogin(String.valueOf(info.getLong("login")))
                    +"\nDEMO"
                    +"\nBalance: "+info.getDouble("balance")
                    +"\nEquity: "+info.getDouble("equity")
                    +"\nAutoTrade: OFF";
                sessionId=token;
                runOnUiThread(()->{
                    if(op!=generation) return;
                    account.setText(display);
                    status.setText("CONNECTED_READ_ONLY".equals(state)
                        ?"Đã kết nối READ_ONLY. AutoTrade: OFF."
                        :"Đã kết nối MT5 DEMO. AutoTrade: OFF.");
                    connect.setEnabled(true);
                    disconnect.setEnabled(true);
                    autoTrade.setEnabled(false);
                });
            }catch(Exception error){
                sessionId="";
                runOnUiThread(()->{
                    if(op!=generation) return;
                    account.setText("Disconnected\nDEMO\nBalance: —\nEquity: —\nAutoTrade: OFF");
                    status.setText("Kết nối thất bại: "+safeError(error));
                    connect.setEnabled(bridgeConfigured());
                    disconnect.setEnabled(false);
                    autoTrade.setEnabled(false);
                });
            }
        });
    }


    private void restoreSession(){
        final String token=encryptedSession.load();
        if(token==null||token.isEmpty()) return;
        final long op=++generation;
        connect.setEnabled(false);
        disconnect.setEnabled(false);
        status.setText("Đang tự khôi phục MT5 DEMO…");
        network.execute(()->{
            try{
                JSONObject reply=request("GET","/mt5/session/account",null,token,125000);
                String state=reply.optString("status","");
                JSONObject info=reply.optJSONObject("account");
                if(!NativeMt5SessionContract.connectedStatus(state)
                    || info==null
                    || !"DEMO".equals(info.optString("trade_mode",""))
                    || !(info.opt("balance") instanceof Number)
                    || !(info.opt("equity") instanceof Number)
                    || reply.optBoolean("order_send_enabled",true)
                    || reply.optInt("orders_sent",-1)!=0
                    || !"OFF".equals(reply.optString("auto_trade",""))){
                    throw new IOException("INVALID_BRIDGE_RESPONSE");
                }
                final String display=("CONNECTED_READ_ONLY".equals(state)?"Read-only":"Connected")
                    +"\nServer: "+info.getString("server")
                    +"\nAccount: "+NativeMt5SessionContract.maskLogin(String.valueOf(info.getLong("login")))
                    +"\nDEMO"
                    +"\nBalance: "+info.getDouble("balance")
                    +"\nEquity: "+info.getDouble("equity")
                    +"\nAutoTrade: OFF";
                sessionId=token;
                runOnUiThread(()->{
                    if(op!=generation) return;
                    account.setText(display);
                    status.setText("Đã tự khôi phục phiên MT5 DEMO. Không cần nhập lại mật khẩu.");
                    connect.setEnabled(true);
                    disconnect.setEnabled(true);
                    autoTrade.setEnabled(false);
                });
            }catch(Exception error){
                sessionId="";
                try{ encryptedSession.clear(); }catch(Exception ignored){ }
                runOnUiThread(()->{
                    if(op!=generation) return;
                    status.setText("Phiên cũ hết hạn hoặc bị thu hồi. Đăng nhập MT5 lại.");
                    connect.setEnabled(bridgeConfigured());
                    disconnect.setEnabled(false);
                    autoTrade.setEnabled(false);
                });
            }
        });
    }

    private void validateConnected(JSONObject reply,String expectedServer,String expectedLogin) throws Exception{
        String state=reply.optString("status","");
        JSONObject info=reply.optJSONObject("account");
        if(!NativeMt5SessionContract.connectedStatus(state)
            || reply.optString("session_id","").length()<32
            || info==null
            || !"DEMO".equals(info.optString("trade_mode",""))
            || !expectedServer.equals(info.optString("server",""))
            || !expectedLogin.equals(String.valueOf(info.optLong("login",-1)))
            || !(info.opt("balance") instanceof Number)
            || !(info.opt("equity") instanceof Number)
            || reply.optBoolean("order_send_enabled",true)
            || reply.optInt("orders_sent",-1)!=0
            || !"OFF".equals(reply.optString("auto_trade",""))){
            throw new IOException("INVALID_BRIDGE_RESPONSE");
        }
        String permission=info.optString("trade_permission","");
        if(!("TRADING_ALLOWED".equals(permission)||"READ_ONLY".equals(permission)))
            throw new IOException("INVALID_BRIDGE_RESPONSE");
    }


    private void disconnect(){
        final String token=sessionId;
        final long op=++generation;
        sessionId="";
        try{ encryptedSession.clear(); }catch(Exception ignored){ }
        password.setText("");
        connect.setEnabled(false);
        disconnect.setEnabled(false);
        autoTrade.setEnabled(false);
        network.execute(()->{
            try{
                if(!token.isEmpty()) request("POST","/mt5/session/disconnect",null,token,15000);
            }catch(Exception ignored){
                // Local opaque token is already discarded from this APK instance.
            }
            runOnUiThread(()->{
                if(op!=generation) return;
                account.setText("Disconnected\nDEMO\nBalance: —\nEquity: —\nAutoTrade: OFF");
                status.setText("Đã ngắt kết nối. AutoTrade: OFF.");
                connect.setEnabled(bridgeConfigured());
            });
        });
    }

    private static String safeError(Exception error){
        String message=error.getMessage();
        if(message!=null && message.matches("[A-Z0-9_]{3,64}")) return message;
        return "REQUEST_FAILED";
    }

    private JSONObject request(String method,String route,JSONObject body,String bearer,int readTimeout) throws Exception{
        if(!bridgeConfigured()) throw new IOException("BRIDGE_UNAVAILABLE");
        URL url=new URL(BuildConfig.CWS_MT5_BRIDGE_BASE_URL+route);
        if(!"https".equalsIgnoreCase(url.getProtocol())) throw new IOException("BRIDGE_UNAVAILABLE");
        HttpURLConnection c=(HttpURLConnection)url.openConnection();
        c.setConnectTimeout(12000);
        c.setReadTimeout(readTimeout);
        c.setInstanceFollowRedirects(false);
        c.setRequestMethod(method);
        c.setRequestProperty("Accept","application/json");
        c.setRequestProperty("Cache-Control","no-store");
        if(bearer!=null) c.setRequestProperty("Authorization","Bearer "+bearer);
        try{
            if(body!=null){
                c.setDoOutput(true);
                c.setRequestProperty("Content-Type","application/json");
                try(OutputStream out=c.getOutputStream()){
                    out.write(body.toString().getBytes(StandardCharsets.UTF_8));
                }
            }
            int code=c.getResponseCode();
            InputStream stream=code>=200&&code<300 ? c.getInputStream() : c.getErrorStream();
            String raw=readBounded(stream);
            JSONObject response=raw.isEmpty()?new JSONObject():new JSONObject(raw);
            if(code<200||code>=300) throw new IOException(response.optString("status","HTTP_ERROR"));
            return response;
        }finally{
            c.disconnect();
        }
    }

    private static String readBounded(InputStream stream) throws Exception{
        if(stream==null) return "";
        try(InputStream in=stream; ByteArrayOutputStream out=new ByteArrayOutputStream()){
            byte[] buffer=new byte[4096];
            int n;
            while((n=in.read(buffer))!=-1){
                if(out.size()+n>262144) throw new IOException("OVERSIZE_RESPONSE");
                out.write(buffer,0,n);
            }
            return out.toString(StandardCharsets.UTF_8.name());
        }
    }

    @Override protected void onDestroy(){
        generation++;
        sessionId="";
        if(password!=null) password.setText("");
        network.shutdownNow();
        super.onDestroy();
    }
}
