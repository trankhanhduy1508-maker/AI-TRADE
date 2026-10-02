package vn.cws.aitrade;

public final class NativeMt5BrokerOption {
    public final String brokerName;
    public final String server;

    public NativeMt5BrokerOption(String brokerName,String server){
        this.brokerName=brokerName;
        this.server=server;
    }

    @Override public String toString(){
        return brokerName+" · "+server;
    }
}
