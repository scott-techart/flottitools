def replace_suffix(name, suffix, suffix_sep_count=1):
    new_name = name.rsplit('_', suffix_sep_count)[0]
    new_name = append_suffix(new_name, suffix)
    return new_name


def append_suffix(name, suffix):
    suffix = suffix.strip('_')
    new_name = '{0}_{1}'.format(name, suffix)
    return new_name
