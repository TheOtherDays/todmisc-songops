#!/usr/bin/python2

import sys
import os
import argparse
import bitstring
# FIXME; fix exit status

sys.path.append(os.path.abspath(os.path.dirname(os.path.realpath(sys.argv[0])) + '/pylsdj'))
sys.path.append(os.path.abspath(os.path.dirname(os.path.realpath(sys.argv[0])) + '/bread'))
sys.path.append(os.path.abspath(os.path.dirname(os.path.realpath(sys.argv[0])) + '/pylsdj/pylsdj'))
sys.path.append(os.path.abspath(os.path.dirname(os.path.realpath(sys.argv[0])) + '/../../pylsdj'))
sys.path.append(os.path.abspath(os.path.dirname(os.path.realpath(sys.argv[0])) + '/../../bread'))

try:
    import pylsdj.savfile as savfile
    from pylsdj.project import load_lsdsng
except ImportError:
    print("Cannot find pylsdj. Please type: git submodule update --init")
    sys.exit(0)


class ArgParser(object):

    def __init__(self, argv=sys.argv, print_args=True):
        self.argv = argv
        # Thanks to https://chase-seibert.github.io/blog/2014/03/21/python-multilevel-argparse.html
        if print_args:
            print("Executing: " + ' '.join(self.argv))
        parser = argparse.ArgumentParser()

        parser.add_argument('command', help='Subcommand to run. Command can be: print_info, split_sav, join_into_sav, test')
        # parse_args defaults to [1:] for args, but you need to
        # exclude the rest of the args too, or validation will fail
        args = parser.parse_args(self.argv[1:2])
        if not hasattr(self, args.command):
            print('Unrecognized command: ' + args.command)
            parser.print_help()
            sys.exit(1)
        # use dispatch pattern to invoke method with same name
        self.command = args.command
        return getattr(self, args.command)()

    def print_info(self):
        parser = argparse.ArgumentParser(prog=self.argv[0] + ' ' + self.argv[1], description='lists songs in a .sav file or print info about a song')
        parser.add_argument('-i', '--input_file', action='store', help='.sav file or .lsdsngfile', required=True)
        # now that we're inside a subcommand, ignore the first
        # TWO argvs, ie the command (git) and the subcommand (commit)
        args = parser.parse_args(self.argv[2:])
        print_info(args.input_file)

    def split_sav(self):
        parser = argparse.ArgumentParser(prog=self.argv[0] + ' ' + self.argv[1], description='extract songs from a .sav')
        parser.add_argument('-i', '--input_file', action='store', help='.sav file', required=True)
        parser.add_argument('-n', '--no_version', help='do not use song version in the filename', action='store_true', default=False)
        parser.add_argument('-d', '--output_dir', help='output directory. default: current directory', default='.')
        parser.add_argument('-s', '--select', help='extract only matching song numbers. eg 1,A', default='')
        args = parser.parse_args(self.argv[2:])
        split_sav(args.input_file, with_version=not(args.no_version), output_dir=args.output_dir, nb_to_dump=args.select)

    def join_into_sav(self):
        parser = argparse.ArgumentParser(prog=self.argv[0] + ' ' + self.argv[1], description='joins several songs or saves into a new save file')
        parser.add_argument('-i', '--input_file', action='store', help=".lsdsng or .sav files", nargs='+', required=True)
        parser.add_argument('-o', '--output_file', required=True, action='store', help="output .sav file")
        parser.set_defaults(cmd='join_into_sav')
        args = parser.parse_args(self.argv[2:])
        join_into_sav(args.input_file, args.output_file, **vars(args))

    def test(self):
        parser = argparse.ArgumentParser(prog=self.argv[0] + ' ' + self.argv[1], description='make tests')
        args = parser.parse_args(self.argv[2:])
        make_tests()


def print_sng_info(sng):
    print(("%2X %8s.%02X %02X" % (0, sng.name, sng.version, sng.size_blks)))


def print_sav_info(sav):
    nb = 0
    for i, project in list(sav.projects.items()):
        if project is not None:
            name = project.name.decode("ASCII").split("\0")[0]
            ver = '%02X' % project.version
            nbb = project.size_blks
            print(("%2X %8s.%s %02X" % (nb, name, ver, nbb)))
        nb += 1


def print_info(ifname):
    (sng, sav) = get_file_type(ifname)
    if sng is None and sav is None:
        raise Exception("Cannot determine the file type of " + str(ifname))
    elif sng is not None:
        print_sng_info(sng)
    elif sav is not None:
        print_sav_info(sav)


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
            fname_out = project.name.split(b'\0')[0].decode("ASCII")

            if(fname_out in names):
                nb = 1
                while fname_out + '(' + str(nb) + ')' in names:
                    nb = nb + 1
                fname_out += '(' + str(nb) + ')'

            names.append(fname_out)

            if(with_version):
                fname_out += '.' + '%02X' % project.version

            fname_out += '.lsdsng'

            fname_out = os.path.join(output_dir, fname_out)
            print(("Saving " + fname_out))
            project.save(fname_out)
        song_nb = song_nb + 1


def empty_save_file_bytes():
    import base64
    import zlib
    # to compress: print(base64.b64encode(zlib.compress(open('/tmp/empty.sav','rb').read(), 9)))
    return zlib.decompress(base64.b64decode(b'eNrt3D1KwwAYBuBooa4eIeAJtD970ia5gF7AwUE3B2c3ndy9gXoFr6DgXTxAfaOC4KbFweZ54OubF76hkEB/CCkKAAAAYNOs1vTX72881ofcV8Bg+YQGgJ9blJNysTcpl8llskm2/eS4S3bJKlkl6363nGZ/mv1Mskm2/eS4S3bJKlkl6363nGV/lv1Mskm2/eS4S3bJKlkl6363nGd/nv1Mskm2mfNj5wq/9wDA/z0AwCDcFUW+BIyK4iXlVdf1IXUAAAbll/cB7K4+ZpD98v11Z/uzbrmKAAAAAAAAAGDYbp6fHh/ub6+vLk6ODhcH+7qu67qu67qu67qub173BCIAAADYPN+etzByB8Q6Ts/++/XgHAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADAlzcmXv4t'))


def clean_filenames(sav):
    for i in range(0, 0x20):
        if i not in sav.projects or sav.projects[i] is None:
            sav.header_block.filenames[i] = 8 * b'\x00'
        else:
            sav.header_block.filenames[i] = sav.header_block.filenames[i].split(b'\x00')[0].ljust(8, b'\x00')
    return sav


def find_next_free_slot(sav):
    free_slot = -1
    for i in range(0, 0x20):
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


def sav_print_callback(msg, curr_step, total_steps, b):
    print("# " + msg + " " + str(curr_step) + "/" + str(total_steps) + " " + str(b))


def get_file_type(ifname):
    sav = None
    sng = None
    if ifname.lower().endswith('.sav'):
        sav = savfile.SAVFile(ifname, callback=sav_print_callback)
    elif ifname.lower().endswith('sng'):
        sng = load_lsdsng(ifname)
    else:
        try:
            sng = load_lsdsng(ifname)
        except:
            sng = None

        if sng is None:
            try:
                sav = savfile.SAVFile(ifname, callback=sav_print_callback)
            except:
                sav = None

    return(sng, sav)


def join_into_sav(ifnames, ofname, **args):
    # FIXME: clean filenames before saving
    import tempfile
    fout = tempfile.NamedTemporaryFile(mode='wb', prefix='todmisc_', suffix='.tmp', delete=False)
    fout.write(empty_save_file_bytes())
    foutname = fout.name
    fout.close()
    target_sav = savfile.SAVFile(foutname)  # FIXME: crappy. We shouldn't need a temp file

    try:
        os.remove(foutname)
    except OSError:
        pass

    nb_songs = 0
    for ifname in ifnames:
        (sng, sav) = get_file_type(ifname)
        if sng is None and sav is None:
            raise Exception("Cannot determine the file type of " + str(ifname))
        elif sng is not None:
            print("Adding " + str(sng.name) + " from " + ifname)
            target_sav = add_sng_to_sav(target_sav, sng)
            nb_songs += 1
        elif sav is not None:
            for i, project in list(sav.projects.items()):
                if project is not None:
                    print("Adding " + str(project.name) + " from " + ifname)
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

    ArgParser((sys.argv[0] + " join_into_sav -i ./test_files/s1.lsdsng ./test_files/s2.lsdsng -o " + os.path.join(tempfile.gettempdir() + "/merged.sav")).split(" "), print_args=True)
    ArgParser((sys.argv[0] + " join_into_sav -i ./test_files/s1.lsdsng " + os.path.join(tempfile.gettempdir() + "/merged.sav -o " + os.path.join(tempfile.gettempdir() + "/merged2.sav"))).split(" "), print_args=True)
    ArgParser((sys.argv[0] + " split_sav -i " + os.path.join(tempfile.gettempdir(), "merged2.sav") + " -d " + tmpdir).split(" "), print_args=True)
    ArgParser((sys.argv[0] + " print_info -i " + os.path.join(tempfile.gettempdir(), "merged2.sav")).split(" "), print_args=True)
    ArgParser((sys.argv[0] + " print_info -i ./test_files/s1.lsdsng").split(" "), print_args=True)

if __name__ == "__main__":
    ArgParser()
