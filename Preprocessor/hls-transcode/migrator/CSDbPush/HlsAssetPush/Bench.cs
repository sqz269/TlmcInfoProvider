namespace HlsAssetPush;

public class Bench
{
    private readonly AppDbContext _context;

    public Bench(AppDbContext context, Dictionary<string, string> idBank)
    {
        _context = context;
    }


}