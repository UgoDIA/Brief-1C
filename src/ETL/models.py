from django.db import models


class Pays(models.Model):
    pays = models.CharField(primary_key=True, max_length=20)

    class Meta:
        db_table = 'pays'


class Produits(models.Model):
    codeproduit = models.CharField(db_column='codeProduit', primary_key=True, max_length=20)  # Field name made lowercase.
    nomproduit = models.CharField(db_column='nomProduit', max_length=20)  # Field name made lowercase.

    class Meta:
        db_table = 'produits'


class Ventes(models.Model):
    nofacture = models.CharField(db_column='noFacture', primary_key=True, max_length=20)  # Field name made lowercase.
    datefacture = models.DateField(db_column='dateFacture')  # Field name made lowercase.
    pays = models.ForeignKey(Pays, models.DO_NOTHING, db_column='pays')

    class Meta:
        db_table = 'ventes'


class Detailsventes(models.Model):
    iddetails = models.AutoField(db_column='idDetails', primary_key=True)  # Field name made lowercase.
    nofacture = models.ForeignKey('Ventes', models.CASCADE, db_column='noFacture')  # Field name made lowercase.
    codeproduit = models.ForeignKey('Produits', models.CASCADE, db_column='codeProduit')  # Field name made lowercase.

    class Meta:
        db_table = 'detailsVentes'
        unique_together = ('nofacture', 'codeproduit')