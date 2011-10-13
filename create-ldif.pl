#! /usr/bin/perl

use strict;

my $fname_addr = $ARGV[0];
my $fname_uid  = '00uid.list';
my $fname_tex  = 'skel.tex';

my $ldif_dc   = 'dc=web,dc=pfs,dc=ipmu,dc=jp';

my $post_ldif = "ldif";
my $post_tex  = "tex";

my @tarr;
my %cur;
my %uids;
my $last_uid = &ReadUid($fname_uid, \%uids);
my @all_new;

open(INDAT, $fname_addr);
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
    &OutLdif($fname_addr, $cur{uname}, $cur{email}, $cur{pass}, $uids{$cur{uname}});
    &ModTexSkel($fname_tex, $fname_addr, $cur{uname}, $cur{email}, $cur{pass});
    push(@all_new, $cur{uname});
}
close(INDAT);
&SaveUid($fname_uid, \%uids);

open(OALL, "> $fname_addr.mga.$post_ldif");
print OALL <<__END_OALL;
dn: cn=all,ou=Groups,$ldif_dc
changetype: modify
add: memberUid
__END_OALL
foreach (@all_new) {print OALL "memberUid: $_\n"; }
print OALL "\n";
close(OALL);

exit;

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
    my ($skel, $supname, $uname, $email, $pass) = @_;
    open(ISKEL, $skel);
    open(ODAT, "> $supname.$uname.$post_tex");
    foreach (<ISKEL>) {
        $_ =~ s/\@\@EMAIL\@\@/$email/;
        $_ =~ s/\@\@USER\@\@/$uname/;
        $_ =~ s/\@\@PASS\@\@/$pass/;
        print ODAT $_;
    }
    close(ODAT);
    close(ISKEL);
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


