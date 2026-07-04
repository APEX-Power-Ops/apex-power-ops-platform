"""Serving-time identity guard for records (Gate 9, Option B)."""

OWNER_ROLES = ("records_owner", "records_fn_owner")


class ServingIdentityError(Exception):
    pass


def assert_serving_identity(conn, sanctioned=("records_api", "records_intake_writer",
                                              "records_auditor")):
    with conn.cursor() as cur:
        cur.execute(
            "select session_user, current_user, "
            "  (select rolsuper from pg_roles where rolname = current_user), "
            "  (select rolbypassrls from pg_roles where rolname = current_user)"
        )
        session_user, cur_user, is_super, is_bypass = cur.fetchone()
    if session_user != cur_user:
        raise ServingIdentityError(
            "session_user (%r) != current_user (%r): a SET ROLE is masking the login"
            % (session_user, cur_user))
    if cur_user not in sanctioned:
        raise ServingIdentityError("identity %r is not a sanctioned serving role" % cur_user)
    if cur_user in OWNER_ROLES:
        raise ServingIdentityError("identity %r is an owner role" % cur_user)
    if is_super:
        raise ServingIdentityError("identity %r is a superuser" % cur_user)
    if is_bypass:
        raise ServingIdentityError("identity %r has BYPASSRLS" % cur_user)
