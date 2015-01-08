#!/usr/bin/python2

import sys, os
import argparse

sys.path.append(os.path.abspath(os.path.dirname(os.path.realpath(sys.argv[0])) + '/pylsdj'))
sys.path.append(os.path.abspath(os.path.dirname(os.path.realpath(sys.argv[0])) + '/bread'))
sys.path.append(os.path.abspath(os.path.dirname(os.path.realpath(sys.argv[0])) + '/../../pylsdj'))
sys.path.append(os.path.abspath(os.path.dirname(os.path.realpath(sys.argv[0])) + '/../../bread'))

try:
    import pylsdj.savfile as savfile
    from pylsdj.project import load_lsdsng
except ImportError:
    print("Cannot find pylsdj. Please type: git submodule update --init")
    sys.exit(0)

def parse_cmd_line_and_execute(args, print_args=False):
    if print_args:
        print("Executing: " + ' '.join(args) )

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='commands')

    help_parser = subparsers.add_parser('help', help='help')
    help_parser.set_defaults(cmd='help')

    join_parser = subparsers.add_parser('join_into_sav', help='joins several songs or saves into a new save file')
    join_parser.add_argument('input_files', action='store', help=".lsdsng or .sav files to merge", nargs='+')
    join_parser.add_argument('-o', '--output_file', required=True, action='store', help="output .sav file")
    join_parser.set_defaults(cmd='join_into_sav')

    split_sav_parser = subparsers.add_parser('split_sav', help='extract songs from a .sav')
    split_sav_parser.add_argument('input_file', action='store', help='.sav file')
    split_sav_parser.add_argument('-n', '--no_version', action='store_true', default=False)
    split_sav_parser.add_argument('-o', '--output_dir', help='output directory. default: current directory', default='.')
    split_sav_parser.add_argument('--only', help='extract only matching song numbers. eg 1,A', default='')
    split_sav_parser.set_defaults(cmd='split_sav')

    info_parser = subparsers.add_parser('print_info', help='lists songs in a .sav file or print info about a song')
    info_parser.add_argument('input_file', action='store')
    info_parser.set_defaults(cmd='print_info')

    test_parser = subparsers.add_parser('test', help='test (debug)')
    test_parser.set_defaults(cmd='test')

    args = parser.parse_args(args=args)

    if args.cmd == "help":
        parser.print_help()
    elif args.cmd == "split_sav":
        split_sav(args.input_file, with_version=not(args.no_version), output_dir=args.output_dir, nb_to_dump=args.only)
    elif args.cmd == "print_info":
        print_info(args.input_file)
    elif args.cmd == "join_into_sav":
        join_into_sav(args.input_files, args.output_file, **vars(args))
    elif args.cmd == "test":
        make_tests()


def print_sav_info(fname):
    sav = savfile.SAVFile(fname)
    nb = 0
    for i, project in list(sav.projects.items()):
        if project is not None:
            name = project.name.decode("ASCII").split("\0")[0]
            ver = '%02X' % project.version
            nbb = project.size_blks
            print(("%2X %8s.%s %02X" % (nb, name, ver, nbb)))
        nb += 1


def print_info(ifile):
        try:
            sng = load_lsdsng(ifile)
            print(("%2X %8s.%02X %02X" % (0, sng.name, sng.version, sng.size_blks)))
        except AssertionError:
            print_sav_info(ifile)


def split_sav(fname, with_version=True, output_dir='.', nb_to_dump=""):
    names = []
    # todo: check that song names are not duplicated (dev done - to test)
    nb_to_dump = nb_to_dump.replace(' ', '')
    if(nb_to_dump != ''):
        nb_to_dump = ',' + nb_to_dump.upper() + ','

    sav = savfile.SAVFile(fname)

    if output_dir != '.':
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

    song_nb = 0
    for i, project in list(sav.projects.items()):
        if project is not None:
            if nb_to_dump != "":
                to_find = ',' + "%X" % song_nb + ','
                if nb_to_dump.find(to_find) == -1:
                    song_nb = song_nb + 1
                    continue
            fname_out = project.name.decode("ASCII").split("\0")[0]

            if(fname_out in names):
                nb = 1
                while fname_out + '(' + str(nb) + ')' in names:
                    nb = nb + 1
                fname_out += '(' + str(nb) + ')'

            names.append(fname_out)

            if(with_version):
                fname_out += '.' + '%02X' % project.version

            fname_out += '.lsdjsng'

            fname_out = os.path.join(output_dir, fname_out)
            print(("Saving " + fname_out))
            project.save(fname_out)
        song_nb = song_nb + 1


def empty_save_file_bytes():
    import base64, zlib
    # to compress: print(base64.b64encode(zlib.compress(open('/tmp/empty.sav','rb').read(), 9)))
    return zlib.decompress(base64.b64decode(b'eNrt3D1KwwAYBuBooa4eIeAJtD970ia5gF7AwUE3B2c3ndy9gXoFr6DgXTxAfaOC4KbFweZ54OubF76hkEB/CCkKAAAAYNOs1vTX72881ofcV8Bg+YQGgJ9blJNysTcpl8llskm2/eS4S3bJKlkl6363nGZ/mv1Mskm2/eS4S3bJKlkl6363nGV/lv1Mskm2/eS4S3bJKlkl6363nGd/nv1Mskm2mfNj5wq/9wDA/z0AwCDcFUW+BIyK4iXlVdf1IXUAAAbll/cB7K4+ZpD98v11Z/uzbrmKAAAAAAAAAGDYbp6fHh/ub6+vLk6ODhcH+7qu67qu67qu67qub173BCIAAADYPN+etzByB8Q6Ts/++/XgHAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADAlzcmXv4t'))


def clean_filenames(sav):
    for i in xrange(0, 0x20):
        if i not in sav.projects or sav.projects[i] is None:
            sav.header_block.filenames[i] = 8 * '\x00'
        else:
            sav.header_block.filenames[i] = sav.header_block.filenames[i].split('\x00')[0].ljust(8, '\x00')
    return sav


def find_next_free_slot(sav):
    free_slot = -1
    for i in xrange(0, 0x20):
        if sav.projects[i] is None:
            free_slot = i
            break
    return free_slot


def add_sng_to_sav(sav, sng):
    # see http://littlesounddj.wikia.com/wiki/File_Management_Structure
    free_slot = find_next_free_slot(sav)

    if free_slot == -1:
        raise InterruptedError(".sav file is full. no more free slot")

    sav.projects[free_slot] = sng

    sav.header_block.filenames[free_slot] = sng.name
    sav.header_block.file_versions[free_slot] = sng.version

    return clean_filenames(sav)


def join_into_sav(ifnames, ofname, **args):
    import tempfile
    fout = tempfile.NamedTemporaryFile(mode='wb', prefix='todmisc_', suffix='.tmp', delete=False)
    fout.write(empty_save_file_bytes())
    foutname = fout.name
    fout.close()
    target_sav = savfile.SAVFile(foutname) # FIXME: crappy. We shouldn't need a temp file

    try:
        os.remove(foutname)
    except OSError:
        pass

    nb_songs = 0
    for ifname in ifnames:
        sav = None
        try:
            sng = load_lsdsng(ifname)
        except AssertionError:
            sng = None

        if sng is None:
            try:
                sav = savfile.SAVFile(ifname)
            except AssertionError:
                sav = None

        if sng is None and sav is None:
            raise Exception("Cannot determine the file type of " + str(ifname))
        elif sng is not None:
            print("Adding " + sng.name + " from " + ifname)
            target_sav = add_sng_to_sav(target_sav, sng)
            nb_songs += 1
        elif sav is not None:
            for i, project in list(sav.projects.items()):
                if project is not None:
                    print("Adding " + project.name + " from " + ifname)
                    target_sav = add_sng_to_sav(target_sav, project)
                    nb_songs += 1

        if target_sav.active_project_number == 255:
            target_sav.active_project_number = nb_songs + 1

    print("Saving to " + ofname)
    target_sav.save(ofname)


def make_tests():
    import tempfile
    tmpdir = os.path.join(tempfile.gettempdir(), "split")
    if not os.path.isdir(tmpdir):
        os.mkdir(tmpdir)
    parse_cmd_line_and_execute(["join_into_sav", "./test_files/s1.lsdsng", "./test_files/s2.lsdsng", "-o", os.path.join(tempfile.gettempdir(), "merged.sav")], print_args=True)
    parse_cmd_line_and_execute(["join_into_sav", "./test_files/s1.lsdsng", os.path.join(tempfile.gettempdir(), "merged.sav"), "-o", os.path.join(tempfile.gettempdir(), "merged2.sav")], print_args=True)
    parse_cmd_line_and_execute(["split_sav", os.path.join(tempfile.gettempdir(), "merged2.sav"), "-o", tmpdir], print_args=True)
    parse_cmd_line_and_execute(["print_info", os.path.join(tempfile.gettempdir(), "merged2.sav")], print_args=True)
    parse_cmd_line_and_execute(["print_info", "./test_files/s1.lsdsng"], print_args=True)

if __name__ == "__main__":
    parse_cmd_line_and_execute(sys.argv[1:])
    sys.exit(0)
