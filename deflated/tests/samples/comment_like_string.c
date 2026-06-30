char * get_pattern(void)

{
    char *local_10 = "scheme://host  // not a comment  /* nor this */";
    return local_10;  // real trailing comment
}
