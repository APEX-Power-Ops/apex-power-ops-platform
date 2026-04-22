"""Quick test of SupabaseStore connectivity."""
import sys
import traceback

outfile = r"C:\APEX Platform\apex-power-ops-platform\apps\mutation-seam\test_output.txt"
sys.path.insert(0, r"C:\APEX Platform\apex-power-ops-platform\apps\mutation-seam")

try:
    from app.db.supabase_store import SupabaseStore, _conn_get
    
    with open(outfile, "w") as f:
        f.write("=== SupabaseStore connectivity test ===\n")
        
        # Test raw connection
        c = _conn_get()
        cur = c.cursor()
        cur.execute("SELECT count(*) FROM seam.apparatus")
        count = cur.fetchone()[0]
        f.write(f"Raw SQL apparatus count: {count}\n")
        cur.close()
        
        # Test store proxy (don't call seed — data already there)
        s = SupabaseStore.__new__(SupabaseStore)
        s.__init__()  # init proxies only, no seed
        
        f.write(f"Store apparatus keys: {list(s.apparatus.keys())}\n")
        app1 = s.apparatus["app-001"]
        f.write(f"app-001: {app1}\n")
        f.write(f"app-001 status: {app1.get('status')}\n")
        
        # Test __contains__
        f.write(f"'app-001' in store.apparatus: {'app-001' in s.apparatus}\n")
        f.write(f"'app-999' in store.apparatus: {'app-999' in s.apparatus}\n")
        
        # Test values()
        vals = s.apparatus.values()
        f.write(f"apparatus.values() count: {len(vals)}\n")
        
        # Test issues (blocking check)
        f.write(f"Issues keys: {list(s.issues.keys())}\n")
        issue2 = s.issues["issue-002"]
        f.write(f"issue-002 blocks_completion: {issue2.get('blocks_completion')}\n")
        
        # Test audit_log (empty)
        f.write(f"Audit log length: {len(s.audit_log)}\n")
        
        # Test idempotency_keys
        f.write(f"Idempotency keys length: {len(s.idempotency_keys)}\n")
        
        # Test write + read-back
        s.apparatus["app-001"] = {**app1, "status": "ready"}
        updated = s.apparatus["app-001"]
        f.write(f"After update, app-001 status: {updated.get('status')}\n")
        
        # Restore
        s.apparatus["app-001"] = {**updated, "status": "not_started"}
        restored = s.apparatus["app-001"]
        f.write(f"After restore, app-001 status: {restored.get('status')}\n")
        
        f.write("\n=== ALL TESTS PASSED ===\n")

except Exception as e:
    with open(outfile, "w") as f:
        f.write(f"ERROR: {e}\n")
        traceback.print_exc(file=f)
