# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models

class Pays(models.Model):
    pays = models.CharField(primary_key=True, max_length=-1)

    class Meta:
        managed = False
        db_table = 'pays'


class Produits(models.Model):
    codeproduit = models.CharField(db_column='codeProduit', primary_key=True, max_length=-1)  # Field name made lowercase.
    nomproduit = models.CharField(db_column='nomProduit', max_length=-1)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'produits'


class Ventes(models.Model):
    nofacture = models.CharField(db_column='noFacture', primary_key=True, max_length=-1)  # Field name made lowercase.
    datefacture = models.DateField(db_column='dateFacture')  # Field name made lowercase.
    pays = models.ForeignKey(Pays, models.DO_NOTHING, db_column='pays')

    class Meta:
        managed = False
        db_table = 'ventes'


class Detailsventes(models.Model):
    iddetails = models.AutoField(db_column='idDetails', primary_key=True)  # Field name made lowercase.
    nofacture = models.ForeignKey('Ventes', models.CASCADE, db_column='noFacture')  # Field name made lowercase.
    codeproduit = models.ForeignKey('Produits', models.CASCADE, db_column='codeProduit')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'detailsVentes'
        unique_together = ('nofacture', 'codeproduit')