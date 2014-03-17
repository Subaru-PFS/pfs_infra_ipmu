#! /usr/bin/perl

use strict;
use Email::Send;
use MIME::Base64 qw(encode_base64);

my $is_reset   = 0;

my $fname_addr = $ARGV[0];
my $fname_uid  = '00uid.list';
my $fname_tex  = 'skel.tex';
my $fname_email = 'skel.email';

my $cmd_latex      = '/usr/bin/pdflatex';
my $cmd_sendmail   = '/usr/bin/sendmail';

if (defined($ARGV[1])) {$is_reset = 1; }

my $ldif_dc   = 'dc=web,dc=pfs,dc=ipmu,dc=jp';

my $post_ldif = "ldif";
my $post_tex  = "tex";

my @tarr;
my %cur;
my %uids;
my $last_uid = &ReadUid($fname_uid, \%uids);
my @all_new;

open(INDAT, $fname_addr);
my ($fout_tex, $fout_email);
foreach (<INDAT>) {
    chomp;
    @tarr = split(/ /, $_);
    if ($#tarr == -1) {next; }
    $cur{email} = $tarr[0];
    if ($#tarr > 0) {$cur{uname} = $tarr[1]; }
    else {$cur{uname} = substr($tarr[0], 0, index($tarr[0], '@')); }
    $cur{pass} = &MakePass();
    if (! defined($uids{$cur{uname}})) {
        $last_uid += 1;
        $uids{$cur{uname}} = $last_uid;
    }
    if ($is_reset == 0) {
        &OutLdif($fname_addr, $cur{uname}, $cur{email}, $cur{pass}, $uids{$cur{uname}});
    } else {
        &OutLdifMod($fname_addr, $cur{uname}, $cur{email}, $cur{pass}, $uids{$cur{uname}});
    }
    $fout_tex = "$fname_addr.$cur{uname}.$post_tex";
    &ModTexSkel($fname_tex, $fout_tex, $cur{uname}, $cur{email}, $cur{pass});
    push(@all_new, $cur{uname});
    # compile PDF and send email
    system($cmd_latex . " $fout_tex");
    # make email
    $fout_email = &ModEmailSkel($fname_email, $fout_tex, $cur{uname}, $cur{email});
    my @email_args;
    push(@email_args, '-i');
    while ($fout_email =~ s/^[\r\n]//g) {}
    my $mailer = Email::Send->new({ mailer => 'Sendmail', mailer_args => \@email_args });
    my $retval = $mailer->send($fout_email);
}
close(INDAT);
&SaveUid($fname_uid, \%uids);

if ($is_reset == 0) {&OutLdifMga($fname_addr, "tech", \@all_new); }

exit;

sub OutLdifMga {
  my ($fname_addr, $add_group, $all_new) = @_;
  open(OALL, ">> $fname_addr.mga.$post_ldif");
  print OALL <<__END_OALL;
dn: cn=$add_group,ou=Groups,$ldif_dc
changetype: modify
add: memberUid
__END_OALL
  foreach (@$all_new) {print OALL "memberUid: $_\n"; }
  print OALL "\n";
  close(OALL);
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
    close(ODAT);
    # attach attachment
    my $buf;
    open(INDAT, $pdfname);
    while(read(INDAT, $buf, 57)) {
        $fout .= encode_base64($buf) . "\n";
    }
    close(INDAT);
    # close MIME
    $fout .= "\n--" . $mime_boundary . "--";
    return $fout;
}

sub OutLdif {
    my ($supname, $uname, $addr, $pass, $uid) = @_;
    if (! defined($uid)) {$uid = 65542; }
    open(ODAT, "> $supname.$uname.$post_ldif");
    print ODAT <<__END_ODAT;
dn: cn=$uname,ou=Users,$ldif_dc
objectClass: top
objectClass: inetOrgPerson
objectClass: posixAccount
uid: $uname
cn: $uname
sn: $uname
uidNumber: $uid
gidNumber: 2000
homeDirectory: /home/$uname
mail: $addr
loginShell: /bin/tcsh
userPassword: $pass

__END_ODAT
    close(ODAT);
}

sub OutLdifMod {
    my ($supname, $uname, $addr, $pass, $uid) = @_;
    if (! defined($uid)) {$uid = 65542; }
    open(ODAT, "> $supname.$uname.$post_ldif");
    print ODAT <<__END_ODAT;
dn: cn=$uname,ou=Users,$ldif_dc
changetype: modify
replace: userPassword
userPassword: $pass

__END_ODAT
    close(ODAT);
}


