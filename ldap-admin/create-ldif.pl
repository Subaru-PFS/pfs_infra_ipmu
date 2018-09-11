#! /usr/bin/perl

use strict;
use Getopt::Long qw(:config posix_default no_ignore_case gnu_compat);
use Email::Send;
use MIME::Base64 qw(encode_base64);
use Cwd;

my $is_reset   = 0;
my $is_disable = 0;

my ($c_reset, $c_disable, @c_group, $c_jira, $c_shell);
GetOptions(
  'reset' => \$c_reset,
  'disable' => \$c_disable,
  'group=s' => \@c_group,
  'jira' => \$c_jira,
  'shell' => \$c_shell,
);
my $fname_addr = shift(@ARGV);
if (defined(shift(@ARGV))) {$c_reset = 1; }

if ((! defined($fname_addr)) || (! -f $fname_addr)) {
  print <<__EOF;
<script> <options> target_list
options:
  --reset : execute reset (password)
  --disable : remove from default groups and set password to invalid
  --group=<str> : enable LDAP group specified by <str>, multiple accepted
  --jira : enable JIRA access
  --shell : define user as shell access group (cannot be used with --reset)
target_list is a filename with lines by "<email> <username> <fullname>"
  uid is taken from '00uid.list' file (last +1)
  default gid is from opt_gid (2000)
  fullname is an option, from third to the end when defined

For new account creation, JPEG image file as <username>.jpg will be loaded as 
jpegPhoto attribute. 
__EOF
  exit;
}

# script defs
my $fname_uid  = '00uid.list';
my $fname_tex  = 'skel.tex';
my $fname_email = 'skel.email';
my $fname_admin = 'skel.admin.email';

# control options
my $opt_ldaphost = 'ldap.pfs.ipmu.jp';
my $opt_ldapadm = 'cn=admin,dc=pfs,dc=ipmu,dc=jp';
my $opt_gid = '2000';
my $opt_invalid = '{SSHA}XXXX';

my @ldefgroup  = ('tech', 'lm'); # default group to be added
my @ldefgroup_jira = ('jira-ldap-users'); # default groupOfMember group (external)
my @ldifgroup_disabled = ('disabled'); # group for disabled accounts
if ($#c_group > -1) {push(@ldefgroup, @c_group); }

my $cmd_add = "ldapadd    -H ldap://${opt_ldaphost} -D ${opt_ldapadm} -W -x -f ";
my $cmd_mod = "ldapmodify -H ldap://${opt_ldaphost} -D ${opt_ldapadm} -W -x -f ";
my $cmd_mod_done = 0;

my $cmd_latex      = '/usr/bin/pdflatex';
my $cmd_sendmail   = '/usr/bin/sendmail';

if (defined($c_reset)) {$is_reset = 1; }
elsif (defined($c_disable)) {$is_disable = 1; }

my $ldif_dc_web = 'dc=web,dc=pfs,dc=ipmu,dc=jp';
my $ldif_dc_shell = 'dc=shell,dc=pfs,dc=ipmu,dc=jp';

my $ldif_dc = defined($c_shell) ? $ldif_dc_shell : $ldif_dc_web;

my $post_ldif = "ldif";
my $post_tex  = "tex";
my $post_pdf  = 'pdf';
my @unlink_tex = ('aux', 'log', 'pdf');

my @tarr;
my %cur;
my %uids;
my $last_uid = &ReadUid($fname_uid, \%uids);
my @all_new;

# for --disable, not need to process email/tex, just output ldif and cmd
if ($is_disable) {
  open(INDAT, $fname_addr);
  my ($fout_tex, $fout_email, @list_uid);
  open(ODAT, ">> $fname_addr.disable.$post_ldif");
  foreach (<INDAT>) {
    chomp;
    @tarr = split(/ /, $_);
    if ($#tarr == -1) {next; }
    $cur{email} = $tarr[0];
    if ($#tarr > 0) {$cur{uname} = $tarr[1]; }
    else {$cur{uname} = substr($tarr[0], 0, index($tarr[0], '@')); }
    print ODAT <<__END_ODAT;
dn: cn=$cur{uname},ou=Users,$ldif_dc
changetype: modify
replace: userPassword
userPassword: $opt_invalid

__END_ODAT
    push(@list_uid, $cur{uname});
  }
  foreach(@ldefgroup) {
    print ODAT "dn: cn=$_,ou=Groups,$ldif_dc_web\n";
    print ODAT "changetype: modify\n";
    print ODAT "delete: memberUid\n";
    foreach (@list_uid) {
      print ODAT "memberUid: $_\n";
    }
    print ODAT "\n";
  }
  foreach (@ldifgroup_disabled) {
    print ODAT "dn: cn=$_,ou=Groups,$ldif_dc_web\n";
    print ODAT "changetype: modify\n";
    print ODAT "add: memberUid\n";
    foreach (@list_uid) {
      print ODAT "memberUid: $_\n";
    }
    print ODAT "\n";
  }
  close(ODAT);
  open(OCMD, ">> $fname_addr.cmd");
  print OCMD "$cmd_mod $fname_addr.disable.$post_ldif\n";
  close(OCMD);
  exit;
}

open(INDAT, $fname_addr);
my ($fout_tex, $fout_email);
foreach (<INDAT>) {
    chomp;
    @tarr = split(/ /, $_);
    if ($#tarr == -1) {next; }
    $cur{email} = $tarr[0];
    if ($#tarr > 0) {$cur{uname} = $tarr[1]; }
    else {$cur{uname} = substr($tarr[0], 0, index($tarr[0], '@')); }
    if ($#tarr > 1) {$cur{fullname} = join(' ', @tarr[2..$#tarr]); }
    else {$cur{fullname} = $cur{uname}; }
    $cur{pass} = &MakePass();
    if (! defined($uids{$cur{uname}})) {
        $last_uid += 1;
        $uids{$cur{uname}} = $last_uid;
    }
    if ($is_reset == 0) {
        &OutLdif($fname_addr, $cur{uname}, $cur{email}, $cur{pass}, $uids{$cur{uname}}, $cur{fullname});
    } else {
        &OutLdifMod($fname_addr, $cur{uname}, $cur{email}, $cur{pass}, $uids{$cur{uname}}, $cur{fullname});
    }
    $fout_tex = "$fname_addr.$cur{uname}.$post_tex";
    &ModTexSkel($fname_tex, $fout_tex, $cur{uname}, $cur{email}, $cur{pass});
    push(@all_new, $cur{uname});
    # compile PDF and send email
    system($cmd_latex . " $fout_tex");
    # make email
    $fout_tex = "$fname_addr.$cur{uname}.$post_pdf";
    $fout_email = &ModEmailSkel($fname_email, $fout_tex, $cur{uname}, $cur{email});
    my @email_args;
    push(@email_args, '-i');
    while ($fout_email =~ s/^[\r\n]//g) {}
    my $mailer = Email::Send->new({ mailer => 'Sendmail', mailer_args => \@email_args });
    my $retval = $mailer->send($fout_email);
    foreach (@unlink_tex) {unlink("$fname_addr.$cur{uname}.$_"); }
    # email to admin
    $mailer = Email::Send->new({ mailer => 'Sendmail', mailer_args => \@email_args });
    $fout_email = &ModEmailAdmin($fname_admin, $cur{uname}, $cur{email});
    while ($fout_email =~ s/^[\r\n]//g) {}
    $retval = $mailer->send($fout_email);
}
close(INDAT);
&SaveUid($fname_uid, \%uids);

if ($is_reset == 0) {
    foreach (@ldefgroup) {
        &OutLdifMga($fname_addr, $_, \@all_new);
    }
    if (defined($c_jira)) {
        foreach (@ldefgroup_jira) {
            &OutLdifGon($fname_addr, $_, \@all_new);
        }
    }
}

exit;

sub OutLdifMga {
  my ($fname_addr, $add_group, $all_new) = @_;
  open(OALL, ">> $fname_addr.mga.$post_ldif");
  print OALL <<__END_OALL;
dn: cn=$add_group,ou=Groups,$ldif_dc_web
changetype: modify
add: memberUid
__END_OALL
  foreach (@$all_new) {print OALL "memberUid: $_\n"; }
  print OALL "\n";
  close(OALL);
  if ($cmd_mod_done == 0) {
    open(OCMD, ">> $fname_addr.cmd");
    print OCMD "$cmd_mod $fname_addr.mga.$post_ldif\n";
    close(OCMD);
    $cmd_mod_done = 1;
  }
}

sub OutLdifGon {
  my ($fname_addr, $add_group, $all_new) = @_;
  open(OALL, ">> $fname_addr.mga.$post_ldif");
  print OALL <<__END_OALL;
dn: cn=$add_group,ou=Groups,$ldif_dc_web
changetype: modify
add: member
__END_OALL
  foreach (@$all_new) {print OALL "member: cn=$_,ou=Users,$ldif_dc\n"; }
  print OALL "\n";
  close(OALL);
  if ($cmd_mod_done == 0) {
    open(OCMD, ">> $fname_addr.cmd");
    print OCMD "$cmd_mod $fname_addr.mga.$post_ldif\n";
    close(OCMD);
    $cmd_mod_done = 1;
  }
}

sub ReadUid {
    my ($fname, $uid) = @_;
    open(INDAT, $fname);
    my @arr;
    my $last = 0;
    foreach (<INDAT>) {
        chomp;
        @arr = split(/ /, $_);
        $uid->{$arr[1]} = $arr[0];
        if ($arr[0] > $last) {$last = $arr[0]; }
    }
    close(INDAT);
    return $last;
}

sub SaveUid {
    my ($fname, $uid) = @_;
    open(ODAT, "> $fname");
    foreach (keys %$uid) {
        print ODAT "$uid->{$_} $_\n";
    }
    close(ODAT);
}

sub MakePass {
    my $num = '0123456789';
    my $alp = 'abcdefghijklmnopqrstuvwxyz';
    my $ALP = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    my $cat = './!"#%&()[]{}$-=,*+';
    my (@arr, $pass);
    my @arr_all;
    push(@arr_all, split(//, $num));
    push(@arr_all, split(//, $alp));
    push(@arr_all, split(//, $ALP));
    push(@arr_all, split(//, $cat));
    my $cid;
    for (0 ... 9) {
        $cid = int(rand($#arr_all));
        push(@arr, $arr_all[$cid]);
        splice(@arr_all, $cid, 1);
    }
    $pass = join('', @arr);
    return $pass;
}

sub ModTexSkel {
    my ($skel, $texname, $uname, $email, $pass) = @_;
    open(ISKEL, $skel);
    open(ODAT, "> $texname");
    foreach (<ISKEL>) {
        $_ =~ s/\@\@EMAIL\@\@/$email/;
        $_ =~ s/\@\@USER\@\@/$uname/;
        $_ =~ s/\@\@PASS\@\@/$pass/;
        print ODAT $_;
    }
    close(ODAT);
    close(ISKEL);
}

sub ModEmailSkel {
    my ($skel, $pdfname, $uname, $email) = @_;
    open(ISKEL, $skel);
    my $fout;
    my $mime_boundary = time();
    foreach (<ISKEL>) {
        $_ =~ s/\@\@EMAIL\@\@/$email/;
        $_ =~ s/\@\@USER\@\@/$uname/;
        $_ =~ s/\@\@BOUNDARY\@\@/$mime_boundary/;
        $fout .= $_;
    }
    close(ISKEL);
    # attach attachment
    my $buf;
    open(INDAT, $pdfname);
    while(read(INDAT, $buf, 57)) {
        $fout .= encode_base64($buf, '') . "\n";
    }
    close(INDAT);
    # close MIME
    $fout .= "\n--" . $mime_boundary . "--";
    return $fout;
}

sub ModEmailAdmin {
    my ($skel, $uname, $email) = @_;
    open(ISKEL, $skel);
    my $fout;
    foreach (<ISKEL>) {
        $_ =~ s/\@\@EMAIL\@\@/$email/;
        $_ =~ s/\@\@USER\@\@/$uname/;
        $fout .= $_;
    }
    close(ISKEL);
    return $fout;
}

sub OutLdif {
    my ($supname, $uname, $addr, $pass, $uid, $fullname) = @_;
    if (! defined($uid)) {$uid = 65542; }
    if (! defined($fullname)) {$fullname = $uname; }
    my $jpegline = "";
    if (-f "${uname}.jpg") {
        $jpegline = "jpegPhoto:< file://" . getcwd() . "/${uname}.jpg";
    }
    open(ODAT, "> $supname.$uname.$post_ldif");
    print ODAT <<__END_ODAT;
dn: cn=$uname,ou=Users,$ldif_dc
objectClass: top
objectClass: inetOrgPerson
objectClass: posixAccount
uid: $uname
cn: $uname
sn: $fullname
uidNumber: $uid
gidNumber: $opt_gid
homeDirectory: /home/$uname
mail: $addr
loginShell: /bin/tcsh
userPassword: $pass
$jpegline

__END_ODAT
    close(ODAT);
    open(OCMD, ">> $supname.cmd");
    print OCMD "$cmd_add $supname.$uname.$post_ldif\n";
    close(OCMD);
}

sub OutLdifMod {
    my ($supname, $uname, $addr, $pass, $uid, $fullname) = @_;
    if (! defined($uid)) {$uid = 65542; }
    open(ODAT, "> $supname.$uname.$post_ldif");
    print ODAT <<__END_ODAT;
dn: cn=$uname,ou=Users,$ldif_dc
changetype: modify
replace: userPassword
userPassword: $pass
__END_ODAT
    if ($uname ne $fullname) {
      print ODAT "-\n";
      print ODAT "replace: sn\n";
      print ODAT "sn: $fullname\n";
    }
    print ODAT "\n";
    close(ODAT);
    if ($cmd_mod_done == 0) {
      open(OCMD, ">> $supname.cmd");
      print OCMD "$cmd_mod $supname.$uname.$post_ldif\n";
      close(OCMD);
      $cmd_mod_done = 1;
    }
}

