-- Fix Supabase auth signup trigger to use schema-qualified enum types.
-- GoTrue executes the auth.users insert under a search_path that does not
-- reliably resolve custom public enum types like user_role.

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, auth, pg_temp
AS $function$
BEGIN
  INSERT INTO public.user_profiles (
    id,
    email,
    full_name,
    role,
    target_certification_level
  )
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1)),
    COALESCE((NEW.raw_user_meta_data->>'role')::public.user_role, 'technician'::public.user_role),
    (NEW.raw_user_meta_data->>'target_certification_level')::public.certification_level
  );
  RETURN NEW;
END;
$function$;